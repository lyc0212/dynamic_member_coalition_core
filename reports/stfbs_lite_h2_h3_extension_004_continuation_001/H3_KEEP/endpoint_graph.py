from copy import deepcopy
class ConnectionRejected(ValueError):pass
def require(b,m):
 if not b:raise ConnectionRejected(m)
def connect(endpoints,intervals,branch):
 ids={};roles=set();out=[]
 for e in endpoints:
  key=e['endpoint_id'];require(key not in ids,'DUPLICATE_ENDPOINT_ID');require(e['branch_id']==branch,'FOREIGN_BRANCH')
  role=(e['target_id'],e['segment_id'],e['stream_id'],e['tick'],e['endpoint_side']);require(role not in roles,'DUPLICATE_ENDPOINT_ROLE');roles.add(role);ids[key]=e
 for row in intervals:
  left=ids[row['left']];right=ids[row['right']]
  require(right['endpoint_side']=='MODEL_INTERVAL_RIGHT','WRONG_RIGHT_ROLE');require(left['segment_id']==right['segment_id']==row['segment_id'],'CROSS_SEGMENT');require(left['team']==right['team'],'CROSS_TEAM');require(left['target_id']==right['target_id'],'CROSS_TARGET');require(right['tick']==left['tick']+1,'NONCONTIGUOUS');require(left['event_order']<right['event_order'],'EVENT_ORDER')
  valid=left['G'] and right['G'] and left['Q']==right['Q']=='PASS';out.append(dict(row,qualified=valid,increment=1 if valid else 0))
 return dict(status='PASS',intervals=out,endpoint_count=len(ids))
