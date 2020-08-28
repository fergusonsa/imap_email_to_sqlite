INSERT INTO email_hosts (
                            host_name
                        )
                        SELECT DISTINCT v.host_name
                          FROM v_email_addresses_with_host v
                               LEFT JOIN
                               email_hosts eh ON v.host_name = eh.host_name
                         WHERE eh.host_name IS NULL;


-- update email_addresses set host_name = substr(lower(email_address), instr(email_address, '@') + 1), email_address = lower(email_address);

-- Set all email hosts to have category = 'spam' if still null and it is from an email in the Bulk Mail folder and the email host is for the from field
update email_hosts set category = 'spam' where (category is null or category = '??') and host_name in (select ea.host_name from email_addresses ea join EmailMessages em on ea.source_uid = em.uid where ea.source_field = 'from' and em.Mailbox = '"Bulk Mail"');
