'''
used with EventBridge, and Lambda Code in this file
give eventbridge permission to trigger this function
give this lambda a role to perform * on EBS
'''
import boto3
from datetime import datetime,timedelta

def lambda_handler(event,context):
    ec2= boto3.client('ec2')
    
    #list all snapshots
    snapshots_res = ec2.describe_snapshots(OwnerId=['self'])

    #Get all instance ID
    active_instance_id=set()
    instances_res = ec2.describe_instances(Filter=[{
            'Name': 'instance-state-code',
            'Values': [
                '16',
            ],
        },{
            'Name': 'instance-state-name',
            'Values': [
                'running',
            ],
        }])

    for reservation in instances_res['Reservation']:
        for instance in reservation['Instances']:
            active_instance_id.add(instance['InstanceId'])

    # Iterate through Snapshots and Delete Snapshot that is more than 30days old, not associated with volume or associated with stale volume
    for snapshot in snapshots_res['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        volume_id := snapshot['VolumeId']

        if not volume_id:
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            print(f'Deleted EBS Snapshot {snapshot_id},Reason: Not attached to volume')
        elif snapshot['StartTime']+timedelta(days=30)< datetime.now():
            ec2.delete_snapshot(SnapshotId=snapshot_id)
            print(f'Deleted EBS Snapshot {snapshot_id},Reason: Snapshot is 30 Days Old')
        else:
            try:
                volume_res = ec2.describe_volumes(VolumeId=[volume_id])
                if not volume_res['Volumes'][0]['Attachment']:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    print(f'Deleted EBS Snapshot {snapshot_id},Reason: Volume associated with Snapshot not attached to ec2')
            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] =='InvalidVolume.NotFound':
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    print(f'Deleted EBS Snapshot {snapshot_id},Reason: Volume associated with Snapshot is Deleted')



''' 
List out all snapshot, filter the stale snapshot and delete snapshot
'''
def