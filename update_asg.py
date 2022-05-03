import boto3, os, time

print("The environment is ", os.environ['ENVIRONMENT'])

if os.environ['ENVIRONMENT'] == 'prod':
	import prod as build
elif os.environ['ENVIRONMENT'] == 'nonprod':
	import nonprod as build
elif os.environ['ENVIRONMENT'] == 'nonprodfailover':
	import nonprodfailover as build
elif os.environ['ENVIRONMENT'] == 'prodfailover':
	import prodfailover as build

ami_id = os.environ['AMI_ID']
print("The AMD generated by Packer is ", os.environ['AMI_ID'])

session = boto3.Session(region_name=build.region)
ec2Client = session.client('ec2')
autoscalingClient = session.client('autoscaling')

#Get AutoScalingGroup, LaunchTemplate from the environment variable import

launchtemplate = build.launch_template
asg = build.auto_scaling_group

#Read in the $Latest Launch Configuration for the non-Prod BG target group and update it to the new AMI that was created via Packer

launchtemplate_version = ec2Client.describe_launch_template_versions(LaunchTemplateId=launchtemplate, Versions=['$Latest'])

print('The current AMI for this launch template is ', launchtemplate_version['LaunchTemplateVersions'][0]['LaunchTemplateData']['ImageId'] )

print('Updating to the new ami,', os.environ['AMI_ID'])

updateversion = ec2Client.create_launch_template_version(
    LaunchTemplateId=launchtemplate,
    SourceVersion='$Latest',
    LaunchTemplateData={
        'ImageId': os.environ['AMI_ID']
    })

updated_launchtemplate_version = ec2Client.describe_launch_template_versions(LaunchTemplateId=launchtemplate, Versions=['$Latest'])

print('The new AMI that will be used for this launch template is ', updated_launchtemplate_version['LaunchTemplateVersions'][0]['LaunchTemplateData']['ImageId'] )

print('We will now start an instance refresh operation to perform a rolling replacement of all EC2 instances registered to this AutoScalingGroup')

#Calling the Start_Instance_Refresh method of AutoScalingGroup.  There is no Waiter Class to guarantee when the ASG picks up and performs the refresh :(

response = autoscalingClient.start_instance_refresh(
    AutoScalingGroupName=asg,
    Strategy='Rolling',
    DesiredConfiguration={
        'LaunchTemplate': {
            'LaunchTemplateId': launchtemplate,
            'Version': '$Latest'
        }
    }
)

#As there is no Waiter class to leverage, just tossing an arbitrary Sleep loop in the code to give the ASG time to refresh the instances
#This is not an absolute guarantee that the instances will be completed with this 5 minute loop, but tests seem to indicate it will have plenty of time

print('Sleeping for 300 seconds to give ASG time to refresh all of the instances within the ASG')

counter = 1
while counter < 301:
    if counter % 10 == 0:
        print(counter)
    time.sleep(1)
    counter += 1

###Determine IP addresses of ASG Instances

print('Pulling all IP addresses of EC2 instances created from this build:')

ec2_instances = autoscalingClient.describe_auto_scaling_instances()

#Dump a list of all ASG instances by EC2 instance ID
instancelist = []
for instance in ec2_instances['AutoScalingInstances']:
    instancelist.append(instance['InstanceId'])

#Ouput the IPs of all instances matching the new AMI_ID - this only outputs the FAILOVER IPs created with the new AMI and not older AMIs that havent been terminated yet

for instance in instancelist:
    ec2 = ec2Client.describe_instances(InstanceIds=[instance])
    for reservation in ec2['Reservations']:
        for instances in reservation['Instances']:
#            #use os.environ['AMI_ID']
             if instances['ImageId'] == os.environ['AMI_ID']:
                print(instances['PrivateIpAddress'])
