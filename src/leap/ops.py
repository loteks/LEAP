""" Module for fundamental evolutionary operators.  You'll find many
traditional selection and reproduction strategies here.

"""

import abc
import itertools
import random
import types
from collections.abc import Iterator

import numpy as np
import toolz
from toolz import curry, topk

from leap.core import Individual


##############################
# do_pipeline method
##############################
# def do_pipeline(population, context, *pipeline):
#     """
#     FIXME commented out because this isn't used anywhere; will uncomment and
#     modify should that change.  MAC.  10/18/19
#     :param population:
#     :param context:
#     :param pipeline:
#     :return:
#     """
#     for op in pipeline:
#         population, context = op(population, context)
#     return population, context


##############################
# Class Operator
##############################
class Operator(abc.ABC):
    """Abstract base class that documents the interface for operators in a LEAP pipeline.

    LEAP treats operators as functions of two arguments: the population, and a "context" `dict` that may be used in
    some algorithms to maintain some global state or parameters independent of the population.

    You can inherit from this class to define operators as classes.  Classes support operators that take extra arguments
    at construction time (such as a mutation rate) and maintain some internal private state, and they allow certain
    special patterns (such as multi-function operators).

    But inheriting from this class is optional.  LEAP can treat any `callable` object that takes two parameters as an
    operator.  You may define your custom operators as closures (which also allow for construction-time arguments and
    internal state), as simple functions (when no additional arguments are necessary), or as curried functions (i.e.
    with the help of `toolz.pipe(...)`.

    """

    @abc.abstractmethod
    def __call__(self, population, *args, **kwargs):
        """
        The basic interface for a pipeline operator in LEAP.

        :param *args: optional variable sequence of arguments
        :param **kwargs: optional dictionary of arguments
        :param population: a list of individuals to be operated upon
        """
        pass


# PROBABLY NOT NEEDED, MAC (12/8/19)
# def next_individual(individual, *args, **kwargs):
#     """ Ensures that the next individual is returned regardless if this argument is a generator, an actual individual,
#         or a (individual, args, kwargs) tuple.
#
#     TODO this could probably become a function decorator
#
#     :param individual:
#     :return: actual individual and *args and **kwards
#     """
#     if isinstance(individual, Individual):
#         return individual, args, kwargs
#     elif isinstance(individual, ()):
#         # if we have a tuple, it's likely an (individual, args, kwargs) passed down the pipeline, so just unpack
#         # that and send it down the line.
#         # FIXME This assumes that the given tuple is of the form (individual, args, kwargs)
#         individual, pipe_args, pipe_kwargs = individual
#         # recursively call this to ensure there's not more unpacking to do
#         return next_individual(individual, (*args, *pipe_args), {**kwargs, **kwargs})
#     if isinstance(individual, types.GeneratorType) or isinstance(individual, Iterator):
#         return next(individual), args, kwargs
#     else:
#         raise RuntimeError('Invalid arguments passed to next_individual()')


def get_context(iterable, **kwargs):
    """ Convenience function for grabbing the the optional context possibly passed down the pipeline

    :param iterable: iterator pointing to a sequence that has been passed in to an operator
    :param kwargs:
    :return: a context object
    """
    try:
        context = next(iterable)
        return {**context, **kwargs}
    except StopIteration:
        # No context as next element so return empty context plus any optional keyword arguments
        return kwargs


##############################
# evaluate operator
##############################
@curry
def evaluate(next_individual):
    """ Evaluate and returns the next individual in the pipeline

    >>> import core, binary_problems

    We need to specify the decoder and problem so that evaluation is possible.

    >>> ind = core.Individual([1,1], decoder=core.IdentityDecoder(), problem=binary_problems.MaxOnes())

    >>> evaluated_ind = next(evaluate(iter([ind])))

    :param next_individual: iterator pointing to next individual to be evaluated
    :param kwargs: contains optional context state to pass down the pipeline in context dictionaries
    :return: the evaluated individual
    """
    while True:
        # "combined" means combining any args, kwargs passed in to this function with those passed in from upstream
        # in the pipeline.
        # individual, pipe_args, pipe_kwargs = next(next_individual)
        individual= next(next_individual)
        individual.evaluate()

        yield individual


##############################
# clone operator
##############################
@curry
def clone(next_individual):
    """ clones and returns the next individual in the pipeline

    >>> import core

    Create a common decoder and problem for individuals.

    >>> original = Individual([1,1])

    >>> cloned_generator = clone(iter([original]))

    :param next_individual: iterator for next individual to be cloned
    :return: copy of next_individual
    """
    while True:
        individual = next(next_individual)

        yield individual.clone()


# ##############################
# # mutate_bitflip operator
# ##############################
@curry
def mutate_bitflip(next_individual, expected=1, *args, **kwargs):
    """ mutate and return an individual with a binary representation

    >>> import core, binary_problems

    >>> original = Individual([1,1])

    >>> mutated_generator = mutate_bitflip(iter([original]))

    :param individual: to be mutated
    :param expected: the *expected* number of mutations, on average
    :param args: optional args
    :param kwargs: optional keyword args
    :return: mutated individual
    """
    def flip(gene):
        if random.random() < probability:
            return (gene + 1) % 2
        else:
            return gene

    while True:
        # individual, pipe_args, pipe_kwargs = next(next_individual)
        foo = next(next_individual)

        # Given the average expected number of mutations, calculate the probability
        # for flipping each bit.
        probability = 1.0 / len(individual.genome) * expected

        individual.genome = [flip(gene) for gene in individual.genome]

        yield individual,  (*pipe_args, *args), {**pipe_kwargs, **kwargs}


# ##############################
# # mutate_gaussian operator
# ##############################
# @curry
# def mutate_gaussian(population, context, prob, std, hard_bounds=(-np.inf, np.inf)):
#     def add_gauss(x):
#         if np.random.uniform() < prob:
#             return x + np.random.normal()*std
#         else:
#             return x
#
#     def clip(x):
#         return max(hard_bounds[0], min(hard_bounds[1], x))
#
#     result = []
#     for ind in population:
#         ind.genome = [clip(add_gauss(x)) for x in ind.genome]
#         ind.fitness = None
#         result.append(ind)
#     return result, context
#
#

@curry
def truncate(previous, size,  *args, **kwargs):
    """ return the `size` best individuals from the given population

        This defaults to (mu, lambda) if `second_population` is not given.

        kwargs['parents'] is an optional population that is "blended" with the
        first for truncation purposes, and is usually used to allow parents
        and offspring to compete. (I.e., mu + lambda).

        FIXME this will also "truncate" *args and **kwargs passed down the line since this expects a sequence
        and not a generator. (Actually, this will be after a pool() call, which returns those, so this should
        work as expected, right?)

        >>> from leap import core, ops, binary_problems
        >>> pop = []
        >>> pop.append(core.Individual([0, 0, 0], decoder=core.IdentityDecoder(), problem=binary_problems.MaxOnes()))
        >>> pop.append(core.Individual([0, 0, 1], decoder=core.IdentityDecoder(), problem=binary_problems.MaxOnes()))
        >>> pop.append(core.Individual([1, 1, 0], decoder=core.IdentityDecoder(), problem=binary_problems.MaxOnes()))
        >>> pop.append(core.Individual([1, 1, 1], decoder=core.IdentityDecoder(), problem=binary_problems.MaxOnes()))

        We need to evaluate them to get their fitness to sort them for truncation.
        >>> i = iter(pop)
        >>> pop = [individual for individual, args, kwargs in evaluate(i)]

        >>> i = iter(pop)
        >>> truncated = truncate(i, 2)


        :param previous: is the tuple from the previous pipeline operator of (population, *args, **kwargs)
        :param size: is what to resize population to
        :param second_population: is optional second population to include
                                  with population for downsizing
        :return: truncated population (plus optional second population)
    """
    if isinstance(previous, tuple):
        # If this is plugged into a pipeline, then previous will contain these items which will have to be unpacked
        population, pipe_args, pipe_kwargs = previous
    else:
        # Else we presume that previous is actually a sequence of individual representing a population
        population = previous
        pipe_args = ()
        pipe_kwargs = {}

    if 'parents' in kwargs:
        return toolz.itertoolz.topk(size, itertools.chain(population,
                                                          kwargs['parents'])), (*args, *pipe_args), {**kwargs, **pipe_kwargs}
    else:
        return toolz.itertoolz.topk(size, population), (*args, *pipe_args), {**kwargs, **pipe_kwargs}





def tournament(population, k=2, context={}, **kwargs):
    """ Selects the best individual from k individuals randomly selected from
        the given population

    :param population: from which to select
    :param k: are randomly drawn from which to choose the best; by default this is 2 for binary tournament selection
    :param context: optional context passed down from the pipeline
    :return: the best of k individuals drawn from population
    """
    while True:
        choices = random.choices(population, k=k)
        best = max(choices)

        # Return the best, and merge any keyword context passed in via the preceding pipeline operators and
        # via the explicit call to this function.
        yield best, {**context, **kwargs}



@curry
def naive_cyclic_selection_generator(population, *args, **kwargs):
    """ Deterministically returns individuals, and repeats the same sequence
    when exhausted.

    This is "naive" because it doesn't shuffle the population between complete
    tours to minimize bias.

    TODO implement non-naive version that shuffles population before first
    iteration and after every complete loop to minimize sample bias.

    >>> import core, ops

    >>> pop = []

    >>> pop.append(core.Individual([0, 0]))
    >>> pop.append(core.Individual([0, 1]))

    >>> cyclic_selector = ops.naive_cyclic_selection_generator(pop)

    :param population: from which to select
    :return: the next selected individual
    """
    iter = itertools.cycle(population)

    while True:
        yield next(iter), args, kwargs


@curry
def pool(next_individual, size, *args, **kwargs):
    """ 'Sink' for creating `size` individuals from preceding pipeline source.

    Allows for "pooling" individuals to be processed by next pipeline
    operator.  Typically used to collect offspring from preceding set of
    selection and birth operators, but could also be used to, say, "pool"
    individuals to be passed to an EDA as a training set.

    >>> import core, ops

    >>> pop = []

    >>> pop.append(core.Individual([0, 0]))
    >>> pop.append(core.Individual([0, 1]))

    >>> cyclic_selector = ops.naive_cyclic_selection_generator(pop)

    >>> pool = ops.pool(cyclic_selector, 3)

    print(pool)
    [Individual([0, 0], None, None), Individual([0, 1], None, None), Individual([0, 0], None, None)]

    :param next_individual: generator for getting the next offspring
    :param size: how many kids we want
    :return: population of `size` offspring
    """
    # TODO this could be more elegant, and I'm not sure about the priority
    # order for what overwrites what for function arguments vs. pipe data.
    final_args = ()
    final_kwargs = {}
    final_pool = []

    for _ in range(size):
        individual, pipe_args, pipe_kwargs = next(next_individual)
        final_args = (*final_args, *pipe_args)
        final_kwargs = {**final_kwargs, **pipe_kwargs}

        final_pool.append(individual)

    # return [next(next_individual) for _ in range(size)], args, kwargs
    return final_pool, final_args, final_kwargs
