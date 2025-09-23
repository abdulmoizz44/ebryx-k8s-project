# GitHub Actions ECR Authentication Troubleshooting

## Current Error: "no basic auth credentials"

This error indicates that AWS credentials are not properly configured in your GitHub repository.

## Step-by-Step Fix:

### 1. Verify GitHub Repository Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Ensure you have these **Repository secrets** configured:

- `AWS_ACCESS_KEY_ID` - Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret access key

**Important**: 
- Secret names are case-sensitive
- Values should not have quotes around them
- No extra spaces before/after the values

### 2. Create AWS IAM User (if not done)

If you haven't created an IAM user yet:

1. Go to AWS Console → IAM → Users
2. Click "Create user"
3. User name: `github-actions-ecr` (or similar)
4. Select "Programmatic access"
5. Attach policy: `AmazonEC2ContainerRegistryPowerUser`
6. Or create custom policy with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:PutImage",
                "ecr:StartImageScan",
                "ecr:DescribeRepositories"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Verify ECR Repository Exists

Make sure your ECR repository exists:

```bash
aws ecr describe-repositories --repository-names k8s-assessment --region us-east-1
```

If it doesn't exist, create it:

```bash
aws ecr create-repository \
    --repository-name k8s-assessment \
    --region us-east-1 \
    --image-scanning-configuration scanOnPush=true
```

### 4. Test Locally (Optional)

Test the same commands locally to verify they work:

```bash
# Configure AWS CLI with your credentials
aws configure

# Test ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 084828598848.dkr.ecr.us-east-1.amazonaws.com

# Test repository access
aws ecr describe-repositories --repository-names k8s-assessment --region us-east-1
```

### 5. Updated Pipeline Features

The updated pipeline now includes:
- **Credential verification**: Checks if AWS credentials work before attempting ECR operations
- **Repository validation**: Verifies the ECR repository exists and is accessible
- **Better debugging**: More detailed output for troubleshooting

### 6. Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Invalid credentials | Double-check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in GitHub secrets |
| Repository not found | Create ECR repository or verify the repository name |
| Permission denied | Ensure IAM user has ECR permissions |
| Wrong region | Verify region is `us-east-1` in both pipeline and ECR repository |
| Expired credentials | Generate new AWS access keys |

### 7. Re-run the Pipeline

After fixing the secrets:
1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Find the failed workflow run
4. Click **"Re-run jobs"**

The new verification steps will help identify exactly what's wrong if the issue persists.

## Next Steps After Success

Once the pipeline works:
1. The image will be tagged with the git commit SHA
2. Use the output image URI in your Helm deployment
3. Update your `values.yaml` with the new image tag

Example:
```yaml
image:
  repository: 084828598848.dkr.ecr.us-east-1.amazonaws.com/k8s-assessment
  tag: "abc123def456..." # From pipeline output
```
