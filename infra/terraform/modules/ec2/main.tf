// EC2 instance that runs Docker with a reverse-proxy serving frontend and API

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] // Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "this" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.sg_id]
  associate_public_ip_address = true
  key_name                    = var.ssh_key_name != "" ? var.ssh_key_name : null

  user_data = templatefile("${path.module}/user_data.tpl", {
    api_image = var.api_image
    web_image = var.web_image
  })

  tags = {
    Name = "${var.project_name}-ec2"
  }
}

resource "aws_eip" "this" {
  count    = var.assign_eip ? 1 : 0
  instance = aws_instance.this.id
  domain   = "vpc"
  tags     = { Name = "${var.project_name}-eip" }
}

