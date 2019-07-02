import boto3
from datetime import timedelta, datetime

ec2_client =  boto3.client('ec2')

def lambda_handler(event, context):
    filters = [{'Name': 'tag:Name', 'Values': ['Lambda created Snapshot']}]

    snapshots = ec2_client.describe_snapshots(Filters=filters)
    days = 14

    for snaps in snapshots['Snapshots']:
        start_time = snaps['StartTime']
        delete_time = datetime.now(start_time.tzinfo) - timedelta(days=days)
        if start_time < delete_time:
            print ('Deleting {id}'.format(id=snaps["SnapshotId"]))
            ec2_client.delete_snapshot(SnapshotId=snaps["SnapshotId"])

