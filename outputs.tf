output "mongo_uri" {
  description="The url to use to connect to the mongo cluster"
  value = mongodbatlas_advanced_cluster.main.connection_strings.0.standard_srv
}