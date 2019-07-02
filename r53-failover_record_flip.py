import boto3
import sys

'''
This script looks for two command line arguments
    -zone ROUTE53ZONEID
    -recordname record.domainname.domain suffix, do not use the trailing period 

This allows for a portable script to pass the specific Zone/Failover record set
The script will then flip the primary/failover records to be the inverse of what they are presently
Simply rerun the script to make them the same as what they were previously
'''


def getopts(argv):
    opts = {}
    while argv:
        if argv[0][0] == '-':
            opts[argv[0]] = argv[1]
            argv = argv[2:]
        else:
            argv = argv[1:]
    return opts

if __name__ == '__main__':
    from sys import argv
    myargs = getopts(argv)

session = boto3.Session(profile_name='identity')
client = session.client('route53')

recordset = client.list_resource_record_sets(HostedZoneId = myargs['-zone'])
for record in recordset['ResourceRecordSets']:
    if record['Name'] == myargs['-recordname'] + '.' and record['Failover'] == 'PRIMARY' :
        primaryrecord = record
    if record['Name'] == myargs['-recordname'] + '.' and record['Failover'] == 'SECONDARY':
        secondaryrecord = record

print('-'*40 , 'These are the current Identity records', '-' * 40)
print(primaryrecord)
print(secondaryrecord)

primaryrecordlist = [d['Value'] for d in primaryrecord['ResourceRecords']]
secondaryrecordlist = [d['Value'] for d in secondaryrecord['ResourceRecords']]

for recordvalue in primaryrecord['ResourceRecords'][0].values():
    primaryrecordvalue = recordvalue

for recordvalue in secondaryrecord['ResourceRecords'][0].values():
    secondaryrecordvalue = recordvalue

deleterecordsfirst = client.change_resource_record_sets(
    HostedZoneId = myargs['-zone'],
    ChangeBatch={
        'Comment': 'Delete Both Records from the zone',
        'Changes': [
            {
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': primaryrecord['Name'],
                    'Type': primaryrecord['Type'],
                    'Failover': primaryrecord['Failover'],
                    'SetIdentifier': primaryrecord['SetIdentifier'],
                    'TTL': primaryrecord['TTL'],
                    'HealthCheckId': primaryrecord['HealthCheckId'],
                    'ResourceRecords': [
                        {
                            'Value': primaryrecordvalue
                        }
                    ]
                }
            },
            {
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': secondaryrecord['Name'],
                    'Type': secondaryrecord['Type'],
                    'Failover': secondaryrecord['Failover'],
                    'SetIdentifier': secondaryrecord['SetIdentifier'],
                    'TTL': secondaryrecord['TTL'],
                    'HealthCheckId': secondaryrecord['HealthCheckId'],
                    'ResourceRecords': [
                        {
                            'Value': secondaryrecordvalue
                        }
                    ]
                }
            }
        ]
    }
)

fliprecords = client.change_resource_record_sets(
    HostedZoneId = myargs['-zone'],
    ChangeBatch={
        'Comment': 'Flipping the active/passive records for maintenance',
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': primaryrecord['Name'],
                    'Type': primaryrecord['Type'],
                    'Failover': 'SECONDARY',
                    'SetIdentifier': 't3-secondary',
                    'TTL': primaryrecord['TTL'],
                    'HealthCheckId': primaryrecord['HealthCheckId'],
                    'ResourceRecords': [
                        {
                            'Value': primaryrecordvalue
                        }
                    ]
                }
            },
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': secondaryrecord['Name'],
                    'Type': secondaryrecord['Type'],
                    'Failover': 'PRIMARY',
                    'SetIdentifier': 't3-primary',
                    'TTL': secondaryrecord['TTL'],
                    'HealthCheckId': secondaryrecord['HealthCheckId'],
                    'ResourceRecords': [
                        {
                            'Value': secondaryrecordvalue
                        }
                    ]
                }
            }
        ]
    }
)

print('-'*40 , 'These are the new Identity records', '-' * 40)

newrecordset = client.list_resource_record_sets(HostedZoneId = myargs['-zone'])
for record in newrecordset['ResourceRecordSets']:
    if record['Name'] == myargs['-recordname'] + '.' and record['Failover'] == 'PRIMARY' :
        print(record)
    if record['Name'] == myargs['-recordname'] + '.' and record['Failover'] == 'SECONDARY':
        print(record)

