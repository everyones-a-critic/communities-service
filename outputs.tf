output "mongo_uri" {
  description = "The url to use to connect to the mongo cluster"
  value       = mongodbatlas_serverless_instance.main.connection_strings_standard_srv
}