dbcook
======

language to describe recipes for persistency of python classes, within their declarations. Independent of the database, hides it as much as technicaly possible - so same recipe / queries can be rendered into SQL/Alchemy (working), or others - RDF, key-value, google-datastore (todo). For big class-hierarchies. Has bitemporal extension, aggregations, polymorphic associations (for multiple inheritance), source-code-generator, etc. Even the query filters can be represented as python expressions..