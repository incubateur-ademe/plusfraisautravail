output "job_definition_id" {
  value       = scaleway_job_definition.this.id
  description = "Pass to `scw jobs definition start <id>` to trigger a run."
}
