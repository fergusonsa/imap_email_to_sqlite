SELECT em.uid,
       em.Mailbox,
       em.sent,
       em.Subject,
       vtea.name AS To_Name,
       vtea.email_address AS To_Email,
       vtea.host_nane AS To_email_host
  FROM EmailMessages em
       LEFT JOIN
       v_to_email_addresses_with_host vtea ON em.uid = vtea.source_uid;


select eh.category, eh.host_name, ea.source_uid, ea.name, ea.email_address, em.subject, em.Mailbox, em.sent from email_addresses ea join EmailMessages em on ea.source_uid = em.uid join email_hosts eh on ea.host_name = eh.host_name
where ea.source_field = 'from' 
order by eh.category, eh.host_name;

select eh.host_name, eh.category, count(em.uid) as num_emails
from email_addresses ea join EmailMessages em on ea.source_uid = em.uid join email_hosts eh on ea.host_name = eh.host_name
where ea.source_field = 'from' 
	and eh.category is null
group by eh.host_name, eh.category
order by eh.host_name;

select eh.category, eh.host_name, ea.source_uid, ea.name, ea.email_address, em.subject, em.Mailbox, em.sent, em.Body from email_addresses ea join EmailMessages em on ea.source_uid = em.uid join email_hosts eh on ea.host_name = eh.host_name
where ea.source_field = 'from' 
and eh.category is null
order by eh.category, eh.host_name;