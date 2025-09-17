output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = module.ec2.public_ip
}

output "public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = module.ec2.public_dns
}

output "frontend_url" {
  description = "URL for the frontend"
  value       = "http://${module.ec2.public_dns}"
}
