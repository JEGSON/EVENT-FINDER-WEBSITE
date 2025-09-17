// Root module wires VPC + SG + EC2 and outputs public URL

module "vpc" {
  source             = "./modules/vpc"
  project_name       = var.project_name
  vpc_cidr           = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr
}

module "sg" {
  source           = "./modules/sg"
  project_name     = var.project_name
  vpc_id           = module.vpc.vpc_id
  allowed_ssh_cidr = var.allowed_ssh_cidr
}

module "ec2" {
  source        = "./modules/ec2"
  project_name  = var.project_name
  subnet_id     = module.vpc.public_subnet_id
  sg_id         = module.sg.sg_id
  instance_type = var.instance_type
  ssh_key_name  = var.ssh_key_name
  assign_eip    = var.assign_eip
  api_image     = var.api_image
  web_image     = var.web_image
}

