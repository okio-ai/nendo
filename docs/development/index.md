# Nendo Development

Developing with and for Nendo Core is straightforward. If you want to get started right away, please refer to the [contribution guidelines](../contributing.md). If you are interested in the design decisions driving our development, or the guidelines for writing good documentation pages, keep reading below.

## Design Decisions

**Why Are Objects Connected by Relationships?**

Objects are connected by relationships to provide additional structure and compatibility with both relational and graph databases. This connection also helps to leave traces of how objects were created from each other, ensuring better traceability and understanding of the object's lifecycle.

**Why Are There Different Kinds of `NendoRelationships`?**

Different kinds of NendoRelationships are necessary to facilitate SQL JOIN operations between objects and their relationships. By having distinct tables for different types of relationships, it becomes clear where to look up the source and target objects corresponding to the respective source and target IDs.

**Why does every object have a free-form `meta` dictionary field?**

The `meta` dictionary field is included in every object to enable developers to add arbitrary information. This feature facilitates the enrichment of the database with additional, non-standard data and aids in querying items within the nendo library.

**What was the `NendoPluginRegistry` introduced for?**

The `NendoPluginRegistry` was introduced to enhance the management and utilization of plugins within Nendo Core. It aims to facilitate the use of remote plugin registries and allows for the integration of additional functions into plugins during their loading process.

**Why is there a `NendoResource` inside the `NendoTrack`?**

The inclusion of `NendoResource` within `NendoTrack` serves multiple purposes: 
1. It supports the storage of various asset types like audio, image, model, and blob.
2. It differentiates between the information related to physical resources (files) and the track information as managed and utilized by the Nendo Core.
3. It enables the mapping of the same physical assets to multiple objects within the nendo library.

**Why is SQLAlchemy used for the default library implementation?**

SQLAlchemy is chosen for several key reasons:
1. It enables quick and straightforward implementation of various DBMS backends.
2. It offers a clean ORM-based approach to map Nendo Core classes to database tables.
3. Its reliability is battle-tested and it includes migration features through `alembic`.


**Why is there a `storage_driver` in the nendo library?**

The `storage_driver` has been introduced to:
1. Decouple the management of structured database information from physical file handling.
2. Enable flexible combinations of different DBMS backends with various storage locations, such as local filesystems, Google Cloud Storage, Amazon S3 buckets, etc.

**Why are there different kinds of plugins (analysis, generate, effect, etc.)?**

Different plugin types like analysis, generate, and effect exist because:
- There are shared functionalities within each plugin class provided by Nendo Core.
- These shared functionalities make the implementation of new plugins more effortless for developers.


## Writing Good Documentation

Writing good documentation is an art in itself. There are way to many awesome tutorials out there which you can easily find using your favorite search engine. The following list of "golden rules" is what we adhered to while writing our documentation and we'd love for you to also keep them in mind when submitting new features to nendo via PRs:

- Keep it short
- Add cross-references
- Provide examples
- Use a spell checker