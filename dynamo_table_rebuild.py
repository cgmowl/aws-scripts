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

secretsmanager = boto3.client(service_name='secretsmanager', region_name=build.secret_region)

def secret_parser(secret_name):
    '''This function exists because the .get_secret_value() function returns it as a giant string and not a dictionary,
    and without knowing how many values are in the string I am parsing it into a dictionary to extract the values via
    variables passed in by the pipeline'''

    parseSecret = secretsmanager.get_secret_value(SecretId=secret_name)

    secretdictionary = {}

    '''the double replace is to strip both quotes out of the string SecretsManager returns but also after multiple runs begins
    to pack spaces in both the key & value. Not entirely clear why, stripping it out for the time being'''
    for item in (parseSecret['SecretString'].strip('{} ').split(',')):
            #print("this is the item: ", item.replace ('"', ""))
            k,v = item.replace('"',"").replace(" ", "").split(':')
            secretdictionary[k] = v

    print("Current values of our secret: ",secretdictionary)

    return(secretdictionary)

def recreate_dynamo(secret_dictionary):
    '''We need to figure out what region that blacklistFullLoad SecretsManager value is pointing at, which is returned
     from the run of the secret_parser, to determine which DynamoDB table to drop and re-create.'''

    if secret_dictionary['blacklistFullLoad'] == "us-east-1":
        dynamo_table_name = build.dynamo_table_east1
        regionname = "us-east-1"
    elif secret_dictionary['blacklistFullLoad'] == "us-east-2":
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


getvalues = secret_parser(build.secret_arn)
dynamorebuild = recreate_dynamo(getvalues)
