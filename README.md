### cfnpkl

cfnpkl is bindings for the [Pkl](https://github.com/apple/pkl) language to generate CloudFormation templates instead of using JSON or YAML. Pkl provides features like:
- Type safety
- Code completion
- Support for reusing templates
- Defining functions for transforming templates
- Modeling inputs to templates instead of the clunk `Ref` syntax

## Getting Started

### Prerequisites
- [Install Pkl](https://pkl-lang.org/main/current/pkl-cli/index.html#installation)

### Create an S3 bucket template

`PklProject`
```pkl
dependencies {
  ["cfn"] { uri = "package://github.com/masp/cfnpkl" }
}
```

`mybucket.pkl`
```pkl
import "@cfn/aws/s3/Bucket.pkl"

Resources {
    ["Bucket"] = new Bucket {
        Properties {
            BucketName = "mybucket"
            AccelerateConfiguration {
                AccelerationStatus = "Enabled"
            }
        }
    }
}
```

Running `pkl eval mybucket.pkl -f json` will generate the following CloudFormation template:

```json
{
  "Resources": {
    "Bucket": {
      "Type": "AWS::S3::Bucket",
      "Properties": {
        "BucketName": "mybucket",
        "AccelerateConfiguration": {
          "AccelerationStatus": "Enabled"
        }
      }
    }
  }
}
```

You can also generate the output in YAML:

```yaml
Resources:
  Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: mybucket
      AccelerateConfiguration:
        AccelerationStatus: Enabled
```

`cfnpkl` can warn you ahead of time if there's a typo in a property name or if you're missing a required property:

`test.pkl`
```pkl
Resources {
    ["Bucket"] = new Bucket {
        Properties {
            BucketName = "mybucket"
            AccelerateConfiguration {
                AccelerationStatus = "Enable" // ERROR: only "Enabled" or "Disabled" allowed!
            }
        }
    }
}
```

`Output`
```
> pkl eval -f json examples/bucket.pkl
–– Pkl Error ––
Expected value of type `"Enabled"|"Suspended"`, but got `"Enable"`.

65 | AccelerationStatus: "Enabled" | "Suspended"
                         ^^^^^^^^^^^^^^^^^^^^^^^
```

### TODO
- [X] Add support for all standard AWS resource providers. See [AWS Resource Types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-template-resource-type-ref.html)
- [ ] Add support for inputs to templates and calculated values
- [ ] Add examples of reusable templates
- [ ] Add automated testing to verify all generated templates are correct and produce valid CloudFormation templates.