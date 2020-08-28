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
