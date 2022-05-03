import boto3, json, os

print("The environment is ", os.environ['ENVIRONMENT'])

if os.environ['ENVIRONMENT'] == 'prod':
	import prod as build
elif os.environ['ENVIRONMENT'] == 'nonprod':
	import nonprod as build
elif os.environ['ENVIRONMENT'] == 'nonprodfailover':
	import nonprodfailover as build
elif os.environ['ENVIRONMENT'] == 'prodfailover':
	import prodfailover as build

#########################################
###
### We are no longer using Secrets Manager to parse what region is considered live
### The dynamo_table_rebuild.py script uses Secrets Manager (legacy config)
### We will simply be reading the region variable imported from build
### We will drop the Dynamo table within that region and rebuild it
### primary region = us-east-2, failover region = us-east-1
### 
##########################################


def recreate_dynamo():
    '''We need to figure out what region that blacklistFullLoad SecretsManager value is pointing at, which is returned
     from the run of the secret_parser, to determine which DynamoDB table to drop and re-create.'''

    if build.region == "us-east-1":
        dynamo_table_name = build.dynamo_table_east1
        regionname = "us-east-1"
    elif build.region == "us-east-2":
        dynamo_table_name = build.dynamo_table_east2
        regionname = "us-east-2"

    dynamodb = boto3.client(service_name='dynamodb', region_name=regionname)
    print("The table that is going to be dropped and recreated is: ",dynamo_table_name)

    '''Attempt to read the table to confirm it exists, then drop the table
    have a built-in sleep of 30sec to give AWS time to drop the table before attempting to create a new 
    table with the same name'''

    try:
        print(dynamodb.describe_table(TableName=build.dynamo_host))
        print("Deleting the table ", dynamo_table_name)

    except:
        print("The table ", dynamo_table_name, " could not be found. Aborting")

    try:
        dynamodb.delete_table(TableName=build.dynamo_host)

        waiter = dynamodb.get_waiter('table_not_exists')

        waiter.wait(
            TableName=build.dynamo_host,
            WaiterConfig={
                'Delay': 20,
                'MaxAttempts': 10
            }
        )

        print("Recreating the table ", dynamo_table_name)

        '''Building the new Dynamo table, HASH key is the primary key, RANGE key is the sort key, need to build all attribute
        definitions before specifying them in the Global Index (source attribute).  Tags is throwing an error, 
        not clear why at the moment'''

        dynamodb.create_table(
            BillingMode='PAY_PER_REQUEST',
            AttributeDefinitions=[
                {
                    'AttributeName': 'emailDomain',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'source',
                    'AttributeType': 'S'
                },
            ],
            KeySchema=[
                {
                    'AttributeName': 'emailDomain',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'email',
                    'KeyType': 'RANGE'
                },
            ],
            TableName=build.dynamo_host,
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'source-email-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'source',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'email',
                            'KeyType': 'RANGE'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL',
                      #  'NonKeyAttributes': [
                      #      'string',
                      #  ]
                    },
                },
            ],
            #Tags=[
            #    {
            #        'Key': 'Application',
            #        'Value': 'TestWebkeyServerCloud'
            #    },
            #    {
            #        'Key': 'Owner',
            #        'Value': 'testwebkeysupport.plm@siemens.com'
            #    },
            #]
        )

    except:
            print("The table ", dynamo_table_name, " could not be deleted, timed out in a deleting state. Aborting")

dynamorebuild = recreate_dynamo()
