// Root module variables

variable "project_name" {
  description = "Name prefix for resources"
  type        = string
  default     = "event-finder"
}

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR for public subnet"
  type        = string
  default     = "10.42.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "Existing AWS Key Pair name to attach for SSH (optional)"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH (22). Set to your IP/CIDR."
  type        = string
  default     = "0.0.0.0/0"
}

variable "api_image" {
  description = "Container image for API (e.g., docker.io/youruser/event-finder-api:latest)"
  type        = string
}

variable "web_image" {
  description = "Container image for web (e.g., docker.io/youruser/event-finder-web:latest)"
  type        = string
}

variable "assign_eip" {
  description = "Assign and allocate an Elastic IP to the instance"
  type        = bool
  default     = true
}

