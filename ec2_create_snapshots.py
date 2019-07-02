import boto3

ec2 = boto3.resource('ec2')
ec2client = boto3.client('ec2')

def lambda_handler(event,context):
    ec2_instances = ec2client.describe_instances()
    for reservation in ec2_instances['Reservations']:
        for instance in reservation['Instances']:
            for volume in instance['BlockDeviceMappings']:
                volumeid = volume['Ebs']['VolumeId']
                snapped = ec2client.create_snapshot(VolumeId=volumeid, Description='Snapshot created by Lambda Function')
                snapshot = ec2.Snapshot(snapped['SnapshotId'])
                snapshot.create_tags(Tags=[{'Key':'Name','Value':'Lambda created Snapshot'}])

