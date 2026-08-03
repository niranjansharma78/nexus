from datetime import datetime,timedelta
from app.core.database import init_db,get_connection
init_db(); now=datetime.now()
evidence=[
('ERP','financial','Large collection recorded','₹8,00,000 received from ABC Industries.','business',now-timedelta(minutes=12),.78,'recorded','ABC Industries',800000,'INR',0,2),
('SMS','financial','Bank credit confirmation','Bank SMS confirms a credit of ₹8,00,000.','digital',now-timedelta(minutes=10),.96,'confirmed','ABC Industries',800000,'INR',0,1),
('Email','communication','Payment advice received','ABC Industries sent payment advice for the same amount.','business',now-timedelta(minutes=8),.93,'confirmed','ABC Industries',800000,'INR',0,2),
('ERP','operations','Dispatch delayed','Dispatch for Order SO-118 is delayed by 4 hours.','business',now-timedelta(minutes=32),.88,'confirmed','Order SO-118',None,None,1,1),
('Calendar','schedule','School meeting tomorrow','Parent meeting is scheduled tomorrow at 10:00 AM.','family',now-timedelta(hours=1),.99,'confirmed','School',None,None,1,2),
('Email','compliance','GST filing reminder','GST filing deadline is tomorrow.','business',now-timedelta(hours=2),.95,'confirmed','GST',None,None,1,1),
('SMS','delivery','Package arriving today','Courier is out for delivery.','personal',now-timedelta(hours=2,minutes=30),.90,'confirmed','Courier',None,None,0,4),
('ERP','production','Production target achieved','SL03 exceeded the day target by 7%.','business',now-timedelta(hours=3),.91,'confirmed','SL03',None,None,0,3),
('Email','communication','Vendor replied','Vendor confirmed revised delivery date.','business',now-timedelta(hours=4),.84,'recorded','Vendor',None,None,0,3),
('Calendar','schedule','Dentist appointment','Appointment scheduled for Saturday at 4:30 PM.','personal',now-timedelta(hours=5),.99,'confirmed','Dentist',None,None,0,4)]
tiles=[('finance','Finance','business',0,'medium',1,0),('business','Business','business',1,'medium',1,0),('family','Family','family',2,'medium',1,0),('calendar','Calendar','digital',3,'medium',1,0),('personal','Personal','personal',4,'medium',1,0),('timeline','Timeline','digital',5,'medium',1,0),('notes','Notes','personal',6,'medium',1,0),('projects','Projects','business',7,'medium',1,0)]
entities=[('abc-industries','ABC Industries','customer','business',88,82,'improving',.89,now.isoformat()),('prime-materials','Prime Raw Materials','supplier','business',67,61,'declining',.81,now.isoformat()),('family-school','School','institution','family',92,90,'stable',.96,now.isoformat()),('sl03','SL03','machine','business',86,None,'improving',.91,now.isoformat()),('dentist','Dentist','service','personal',90,87,'stable',.93,now.isoformat()),('vendor-x','Vendor X','supplier','business',72,68,'declining',.76,now.isoformat())]
notes=[('Review packaging idea next week','business',1,0,now.isoformat()),('Call banker regarding LC','personal',0,0,now.isoformat())]
with get_connection() as c:
 if c.execute('select count(*) from evidence').fetchone()[0]==0:c.executemany('insert into evidence(source,evidence_type,title,summary,domain,occurred_at,confidence,status,entity_name,amount,currency,requires_decision,priority) values(?,?,?,?,?,?,?,?,?,?,?,?,?)',[(a,b,c1,d,e,f.isoformat(),g,h,i,j,k,l,m) for a,b,c1,d,e,f,g,h,i,j,k,l,m in evidence])
 if c.execute('select count(*) from workspace_tiles').fetchone()[0]==0:c.executemany('insert into workspace_tiles values(?,?,?,?,?,?,?)',tiles)
 if c.execute('select count(*) from entities').fetchone()[0]==0:c.executemany('insert into entities(entity_key,name,entity_type,domain,health_score,relationship_score,trajectory,confidence,updated_at) values(?,?,?,?,?,?,?,?,?)',entities)
 if c.execute('select count(*) from notes').fetchone()[0]==0:c.executemany('insert into notes(text,domain,pinned,archived,created_at) values(?,?,?,?,?)',notes)
print('Nexus DP1-B002 database ready')
