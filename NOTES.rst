Notes
=====

Strata's supposed to be for big projects. It's not meant to replace
ConfigParser or argparse. Rather, build on those modules, and the
myriad other ways projects do their configuration.

Configuration here refers more to runtime/in-process configuration,
typically at application start-up time, as opposed to deployment-time
configuration, or configuration management/versioning
(puppet/cfengine-like things).


Motivation
----------

As any sufficiently mature and featureful software suite will
demonstrate, complexity of "configuration" scales superlinearly when
compared to the complexity of the software itself. Many
languages/developers have more or less figured out how to factor and
modularize internal application complexities. However, when it comes
to exposing an interface to those complexities, the inherent flatness
of an interface often results in a projection that is increasingly
unintuitive for users and unsupportable for developers.

Here's a very basic example: a hypothetical command-line application
needs a working directory to perform its operations. This working
directory can be specified on the command-line as an argument, in an
INI file in the current working directory (if one exists), a
home-folder "dotfile", and a default generated based on hostname and
username.

Strata addresses configuration holistically, providing a framework for
negotiating a deterministic and introspective union of an
application's interface implementation.


Design
------

To achieve the goals above, Strata introduces a three-dimensional
model for decomposing software configuration. The three dimensions
are:

1. Variables
2. Layers
3. Environments

A Variable represents a value which is necessary for initializing a
configuration. In the example above, the working directory is a
Variable.

A Layer is a source of values for one or more Variables. A Layer
represents and implements one method of providing a value per Variable
supported by that Layer. For instance, the configuration in the
example above would have one layer for command-line arguments.

An environment is really just an ordered set of Layers that is
appropriate for a given environment. Examples of environments would be
development, test, load-testing, and production; in the test
environment, a 'mocks' Layer might be appropriate, but not in
production.


TODO
====

* how to avoid global state? ConfigSpec?
* built-in vs. overridable variables?
* automatic listing of Layer providing?


strategy
--------

1.1 collect feature flags from overrides, params, args.
1.2 explicit feature flag step, remove disabled things from dep graph

Concern: shared variables can't be removed outright. needs to remove
references, not whole variables.

2.1 have a feature flag layer that detects disabled features and
provides NullConfigs for end deps
2.2 enable early provides execution (execute a layer's attempt at
providing a variable as soon as its dependency is available)

Concern: how to mark certain provides as safe to execute eagerly
rather than lazily? It only makes a difference if dependencies are
added/removed during fulfillment.

* dynamic depends?


Validators
----------

* Quantity

  * Doesn't matter (default)
  * One or none
  * One or more
  * Zero or more
  * Specific number
  * Singular scalar (maybe?)

* File-based

  * is file/dir/link
  * is readable/writable
