#! /usr/bin/env python

##############################################################################
#
#   LEAP - Library for Evolutionary Algorithms in Python
#   Copyright (C) 2004  Jeffrey K. Bassett
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
##############################################################################

# Python 2 & 3 compatibility
from __future__ import print_function

import sys
import random
import string
import copy
import math

from LEAP.individual import Individual
from LEAP.selection import DeterministicSelection
from LEAP.ea import GenerationalEA




#############################################################################
#
# printPopulation
#
#############################################################################
def printPopulation(population, generation = None):
    for index, individual in enumerate(population):
        if generation != None:
            print("Gen:", generation, end='')
        print("Ind:", index, "", individual)



#############################################################################
#
# ea
#
##############################################################################
class g2pMetaEA(GenerationalEA):
    def __init__(self, encoding, pipeline, popSize, validationProblem, \
                 initPipeline=DeterministicSelection(), \
                 indClass=Individual, \
                 initPopsize=None, halt=None, validationFrequency=20):
        GenerationalEA.__init__(self, encoding, pipeline, popSize, \
                 initPipeline=initPipeline, indClass=indClass, \
                 initPopsize=initPopsize, halt=halt)
        self.validationProblem = validationProblem
        self.validationFrequency = validationFrequency
        self.validationBOG = None  # Best of all validations for a generation
        self.validationBSF = None
        self.bogValidation = None  # Validation of usual best-of-generation


    def validate(self):
        """
        Perform the validation step.  Evaluate the individuals on a different
        set of problems that have never been used for fitness calculations
        """
        bestIndex = None
        bestVal = None
        for i in range(len(self.population)):
            ind = self.population[i]
            # Evaluating the individual won't work, so I'll do this
            val = self.validationProblem.evaluate(self.encoding.decodeGenome(ind.genome))

            if bestVal == None or self.encoding.cmpFitness(bestVal, val) == -1:
                bestVal = val
                bestIndex = i

        return (bestVal, self.population[bestIndex])


    def startup(self):
        self.validationBOG = (None, [])  # Best of all validations for a generation
        self.validationBSF = (None, [])
        self.bogValidation = None  # Validation of usual best-of-generation
        GenerationalEA.startup(self)


    def calcStats(self):
        GenerationalEA.calcStats(self)

        if self.generation % self.validationFrequency == 0:
            tempValid = self.validate()
            print(tempValid)
            self.validationBOG = (tempValid[0], tempValid[1])
            if self.validationProblem.cmpFitness(self.validationBSF[0],
                                                 self.validationBOG[0]) == -1:
                self.validationBSF = self.validationBOG

        # Run validation on the bestOfGen individual
        self.bogValidation = self.validationProblem.evaluate(
                               self.encoding.decodeGenome(self.bestOfGen.genome))


    def printStats(self):
        GenerationalEA.printStats(self)
        print("Gen:", self.generation, " Ind: BOGV  Val:", self.bogValidation)
        if self.generation % self.validationFrequency == 0:
            print("Gen:", self.generation, " Ind: VBOG ", self.validationBOG[1], \
                  "Val:", self.validationBOG[0])




#############################################################################
#
# Main
#
#############################################################################
if __name__ == '__main__':
    from LEAP.problem import valleyFunctor
    from LEAP.problem import valleyMaximize
    from LEAP.problem import valleyBounds
    from LEAP.problem import FunctionOptimization
    from LEAP.selection import *
    from LEAP.operators import *
    from LEAP.survival import *
    from LEAP.halt import HaltWhenNoChange
    from LEAP.halt import HaltAfterGeneration

    from LEAP.Domains.Translated.translatedProblem import TranslatedProblem

    from LEAP.Contrib.g2pMapping.g2pMappingProblem import g2pMappingProblem
    from LEAP.Contrib.g2pMapping.g2pMappingEncoding import g2pMappingEncoding
    from LEAP.Contrib.g2pMapping.g2pMappingGaussianMutation import g2pMappingGaussianMutation
    from LEAP.Contrib.g2pMapping.g2pMappingMagnitudeGaussianMutation import g2pMappingMagnitudeGaussianMutation
    from LEAP.Contrib.g2pMapping.g2pMappingVectorGaussianMutation import g2pMappingVectorGaussianMutation

    numDimensions = 2
    numVectorsPerDimension = 10
    numVectors = numDimensions * numVectorsPerDimension

    # ----- SubEA -----
    subPopSize = 50
    subPmutate = 1.0 / numVectors
    numTrainingExamples = 5
    numValidationExamples = 5
    subGensWithoutImprovement = 40
    subHalt = HaltWhenNoChange(subGensWithoutImprovement)
    #subHalt = HaltAfterGeneration(40)

    # subProblem
    valleyDirection = [1.0] * (numDimensions)
    valleyFunc = valleyFunctor(valleyDirection)
    #bounds = [valley2Bounds[0]] * numDimensions
    valleyMax = valleyMaximize
    subProblem = FunctionOptimization(valleyFunc, maximize = valleyMax)

    # training set
    # Translate within [-15, 15] along each dimension.
    trainingExamples = []
    for i in range(numTrainingExamples):
        trans = [random.uniform(-15, 15) for i in range(numDimensions)]
        trainingExample = TranslatedProblem(subProblem, trans)
        trainingExamples += [trainingExample]

    # validation set
    validationExamples = []
    for i in range(numValidationExamples):
        trans = [random.uniform(-15, 15) for i in range(numDimensions)]
        validationExample = TranslatedProblem(subProblem, trans)
        validationExamples += [validationExample]

    # subPipeline
    subPipeline = TournamentSelection(2)
    subPipeline = CloneOperator(subPipeline)
    subPipeline = NPointCrossover(subPipeline, 1.0, 2)
    #subPipeline = UniformCrossover(subPipeline, 1.0, 0.5)
    subPipeline = BitFlipMutation(subPipeline, subPmutate)


    subEncoding = None  # Will be set by the metaEA
    subEA = GenerationalEA(subEncoding, subPipeline, subPopSize,\
                                halt=subHalt)
    #subEA = GenerationalEA(subEncoding, subPipeline, subPopSize, \
    #                             indClass=Price.PriceIndividual)

    # ----- MetaEA -----
    metaPopSize = 5
    metaGenerations = 1
    magInitRange = (-4, 4)   # the magnitude is an exponent
    vectorInitRange = (-1.0, 1.0)
    magSigma = 1.0
    vectorSigma = 1.0  # From Siggy's paper
    metaPmutate = 1.0 / numVectors
    validationFrequency = 20

    # metaProblem
    metaProblem = g2pMappingProblem(trainingExamples, subEA)
    validationProblem = g2pMappingProblem(validationExamples, subEA)

    # metaEncoding
    initRanges = [magInitRange] + [vectorInitRange] * numDimensions
    #bounds = initRanges   # I'm not sure if these really work
    bounds = None
    metaEncoding = g2pMappingEncoding(metaProblem, numVectors,
                                        initRanges, bounds)

    # metaPipeline
    # Parent Selection (necessary)
    metaPipeline = TournamentSelection(2)
    #metaPipeline = ProportionalSelection()
    #metaPipeline = TruncationSelection(popSize/2)
    #metaPipeline = RankSelection()
    #metaPipeline = DeterministicSelection()

    # Clone (necessary)
    metaPipeline = CloneOperator(metaPipeline)

    # Crossover (not strictly necessary)
    metaPipeline = NPointCrossover(metaPipeline, 1.0, 2)
    #metaPipeline = UniformCrossover(metaPipeline, 1.0, 0.5)

    # Mutation (not strictly necessary, but you'll almost certainly want it)
    metaPipeline = g2pMappingGaussianMutation(metaPipeline, vectorSigma,
                                                  metaPmutate, bounds)
    #metaPipeline = g2pMappingMagnitudeGaussianMutation(metaPipeline,
    #                                      magSigma, metaPmutate, bounds)
    #metaPipeline = g2pMappingVectorGaussianMutation(metaPipeline,
    #                                      vectorSigma, metaPmutate,
    #                                      bounds)

    # Survival selection (not necessary)
    # If you do use this, you probably want DeterministicSelection above.
    #metaPipeline = ElitismSurvival(metaPipeline, 2)
    #metaPipeline = MuPlusLambdaSurvival(metaPipeline, popSize, popSize*2)
    #metaPipeline = MuCommaLambdaSurvival(metaPipeline, popSize, popSize*10)

    metaEA = g2pMetaEA(metaEncoding, metaPipeline, metaPopSize, \
                           validationProblem=validationProblem, \
                           validationFrequency=validationFrequency)

    profiling = False
    if profiling:
        import profile
        #profile.run('ea(params)', 'eaprof')
        profile.run('metaEA.run(metaGenerations)', 'eaprof')
    
        import pstats
        p = pstats.Stats('eaprof')
        p.sort_stats('time').print_stats(20)
    else:
        metaEA.run(metaGenerations)

