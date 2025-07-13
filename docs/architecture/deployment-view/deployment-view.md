# Deployment view

![Deployemnt Diagram](/docs/architecture/deployment-view/deployment.png)

We deploy on AWS using:

-   **CloudFront + S3** for static assets (React bundle).
-   **EKS (Kubernetes)** for both frontend and API pods, behind an ALB with HTTPS termination.
-   **RDS (PostgreSQL)** in a private subnet, with automated backups and Multi-AZ for high availability.

| Component       | Location                   | Notes                          |
| --------------- | -------------------------- | ------------------------------ |
| React app       | S3 + CloudFront CDN        | Globally cached, TTL = 5 min   |
| FastAPI service | EKS (2 pods, 500 m/256 Mi) | Auto-scale on CPU > 60 %       |
| PostgreSQL RDS  | Private subnet, Multi-AZ   | Backups daily, 7-day retention |

This setup lets the customer spin up the entire stack via our Terraform module in their own AWS account—only configuration values (VPC IDs, domain names, secrets) need to be provided.
