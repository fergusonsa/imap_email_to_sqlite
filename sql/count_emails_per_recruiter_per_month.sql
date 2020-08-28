select eh.category, ea.source_uid, ea.name, ea.email_address, em.subject, em.Mailbox, em.sent, strftime('%y', em.sent) as Year, strftime('%m',em.sent) as month, em.Body from email_addresses ea join EmailMessages em on ea.source_uid = em.uid join email_hosts eh on ea.host_name = eh.host_name
where eh.category = 'recruiter'
order by Year desc, month desc;


select sent, strftime('%Y', sent), strftime('%Y', 'now') from EmailMessages;