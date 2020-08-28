#!/usr/bin/python3
import argparse
import email
import imaplib
import logging
import pathlib
import re
import sqlite3

import utils.common_utils
import utils.configuration

logger = logging.getLogger(__name__)


# For Yahoo Mail:
# If you still want to use an app that uses less secure sign in,
# go to https://login.yahoo.com/account/security#other-apps and turn on
# "Allow apps that use less secure sign in". This is not recommended and may
# leave your account more vulnerable to compromise. To learn more, please visit
# our help page: https://help.yahoo.com/kb/SLN27791.html.


def save_temporary_uids_to_db(db_connection, uids):
    formatted_uids = [(uid,) for uid in uids]
    # logger.debug('un-formatted uids to insert: {}'.format(uids))
    # logger.debug('formatted uids to insert: {}'.format(formatted_uids))
    response = db_connection.executemany("insert into Temporary_UIDs(UID) values (?)", formatted_uids)
    logger.debug('insert temporary uids response rowcount: {}'.format(response.rowcount))
    db_connection.commit()


def clear_temporary_uids_table(db_connection):
    response = db_connection.execute('delete from Temporary_UIDs')
    logger.debug('Deleted {} rows from the Temporary_UIDs table.'.format(response.rowcount))
    db_connection.commit()


def get_list_of_uids_not_in_db(db_connection, uids):
    clear_temporary_uids_table(db_connection)
    save_temporary_uids_to_db(db_connection, uids)
    response = db_connection.execute('SELECT Temporary_UIDs.UID FROM Temporary_UIDs LEFT JOIN EmailMessages ON '
                                     'Temporary_UIDs.UID = EmailMessages.UID WHERE EmailMessages.UID IS NULL;')
    new_uids = [row[0] for row in response.fetchall()]
    clear_temporary_uids_table(db_connection)
    return new_uids


def save_email_to_db(db_connection, uid, mailbox_name, email_msg):
    try:
        response = db_connection.execute('insert into EmailMessages values(?, ?, ?, ?, ?, ?, ?, ?, ?);',
                                         (uid,
                                          email_msg.get('To', ''),
                                          email_msg.get('From'),
                                          email_msg.get('Subject'),
                                          email_msg.get('CC'),
                                          email_msg.get('Date'),
                                          email_msg.get('Received'),
                                          mailbox_name,
                                          get_message_body(email_msg)))
        logger.debug('insert email message response rowcount: {}'.format(response.rowcount))
        logger.debug('inserted email message with uid {} from mailbox {}'.format(uid.decode(), mailbox_name))
        db_connection.commit()
    except sqlite3.InterfaceError as ie:
        logger.warning('Error {}: Could not save message from mailbox {} with uid {}, To: {}, From: {}, subject: "{}"'.
                       format(ie, mailbox_name, uid.decode(), email_msg.get('To'), email_msg.get('From'),
                              email_msg.get('Subject', '').decode()))
    except sqlite3.IntegrityError as ie:
        logger.warning('Error {}: Could not save message from mailbox {} with uid {}, To: {}, From: {}, subject: "{}"'.
                       format(ie, mailbox_name, uid.decode(), email_msg.get('To'), email_msg.get('From'),
                              email_msg.get('Subject', '').decode()))


def list_mailboxes(mail):
    for i in mail.list()[1]:
        parts = i.decode().split(' "/" ')
        logger.debug(parts[0] + " = " + parts[1])


def get_message_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get('Content-Disposition'))
            # look for plain text parts, but skip attachments
            if content_type == 'text/plain' and 'attachment' not in disposition:
                charset = part.get_content_charset()
                # decode the base64 unicode byte string into plain text
                if charset:
                    body = part.get_payload(decode=True).decode(encoding=charset, errors="ignore")
                else:
                    logger.debug('Unable to get charset for message body!')
                    body = part.get_payload(decode=True).decode(errors="ignore")
                # if we've found the plain/text part, stop looping through the parts
                break
    else:
        # not multipart - i.e. plain text, no attachments
        charset = msg.get_content_charset()
        if charset:
            body = msg.get_payload(decode=True).decode(encoding=charset, errors="ignore")
        else:
            logger.debug('Unable to get charset for message body!')
            body = msg.get_payload(decode=True).decode(errors="ignore")
    return body


def copy_emails_from_imap_to_db(config):
    imap_server_host = config['imap']['imap_server_host']
    imap_server_port = config['imap']['imap_server_port']
    username = config['imap']['username']
    password = config['imap']['password']
    with imaplib.IMAP4_SSL(imap_server_host, imap_server_port) as imap_server:
        if imap_server:
            logger.debug('successfully got imap server {} {}'.format(imap_server_host, imap_server_port))
        else:
            logger.error('no imap server returned! Could not connect to {} {}'.format(imap_server_host,
                                                                                      imap_server_port))
            return
        response = imap_server.login(username, password)
        logger.debug('Response from login to imap server with user {}: {}'.format(username, response))
        # TODO Should confirm that login was successful! Expected response: ('OK', [b'LOGIN completed'])

        search_filter = '(SINCE 01-Apr-2015)'
        db_path_str = config['sqlite_db']['path']
        db_path = pathlib.Path(db_path_str).expanduser()
        if not db_path.is_file():
            logger.error('Cannot find SQLite db file {}'.format(db_path))
            return
        with sqlite3.connect(db_path) as db_conn:
            db_conn.row_factory = sqlite3.Row
            for imap_mailbox_info in imap_server.list()[1]:
                if imap_mailbox_info:
                    decoded_mailbox_info = imap_mailbox_info.decode()
                    mailbox_name_parts = decoded_mailbox_info.split('"''')

                    mailbox_name = mailbox_name_parts[1]
                    cleaned_mailbox_name = mailbox_name.strip('"''')
                    imap_server.select(mailbox_name, readonly=True)
                    # noinspection PyTypeChecker
                    response, msg_uids_bytes = imap_server.uid('search', None, search_filter)
                    msg_uids = msg_uids_bytes[0].split()
                    logger.info('Mailbox {} has {} messages for the filter {}'.format(mailbox_name,
                                                                                      len(msg_uids), search_filter))
                    if len(msg_uids):
                        uids_to_fetch = get_list_of_uids_not_in_db(db_conn, msg_uids)
                        logger.info('{} new messages in {} mailbox to insert into db'.format(len(uids_to_fetch),
                                                                                             cleaned_mailbox_name))
                        # logger.debug('UIDs to fetch and insert: {}'.format(uids_to_fetch))
                        for uid in uids_to_fetch:
                            response, fetch_data = imap_server.uid('fetch', uid, '(RFC822)')
                            try:
                                email_msg = email.message_from_bytes(fetch_data[0][1])
                                save_email_to_db(db_conn, uid, cleaned_mailbox_name, email_msg)
                            except AttributeError as ae:
                                logger.warning('Unable to get email message with UID {} in mailbox {}'.format(
                                    uid, cleaned_mailbox_name), ae)
        imap_server.close()


def process_email_addresses(config):
    db_path_str = config['sqlite_db']['path']
    db_path = pathlib.Path(db_path_str).expanduser()
    if not db_path.is_file():
        logger.error('Cannot find SQLite db file {}'.format(db_path))
        return
    regex = r"[\"\']{0,2}(?P<name>[a-zA-Z0-9][a-zA-Z0-9@., ]*)?[\"\']{0,2}\s+<?(?P<address>[a-zA-Z0-9_.+-]+@(?P<hostname>[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+))>?(,\s\r\n)*"
    with sqlite3.connect(db_path) as db_connection:
        db_connection.row_factory = sqlite3.Row
        # For all the non-empty To, From, & CC fields
        for view_name in ['select_missing_to_fields', 'select_missing_from_fields', 'select_missing_cc_fields']:
            response = db_connection.execute('SELECT UID, field, field_name from {};'.format(view_name))
            row_count = 0
            inserted = 0
            for row in response:
                row_count = row_count + 1
                uid = row['UID']
                field_name = row['field_name']
                value = row['field']
                matches = re.finditer(regex, value)
                for match_num, match in enumerate(matches, start=1):
                    parts = match.groupdict()
                    logger.debug(
                        "For row # {} of entries for {}: Match {match_num} was found at {start}-{end}: {match}".format(
                            row_count, view_name, match_num=match_num,
                            start=match.start(),
                            end=match.end(),
                            match=match.group()))
                    db_connection.execute('insert into email_addresses values(?, ?, ?, ?, ?)',
                                          (uid, field_name, parts['address'], parts.get('name'), parts['hostname']))
                    inserted = inserted + 1
            logger.info('For view {}, inserted {} records from {} rows'.format(view_name, inserted, row_count))
        db_connection.commit()


def test_process(config):
    db_path_str = config['sqlite_db']['path']
    db_path = pathlib.Path(db_path_str).expanduser()
    if not db_path.is_file():
        logger.error('Cannot find SQLite db file {}'.format(db_path))
        return
    with sqlite3.connect(db_path) as db_connection:
        db_connection.row_factory = sqlite3.Row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    exclusive_arguments = parser.add_mutually_exclusive_group()
    parser.add_argument("-v", dest="verbose", action="store_true", help="Flag to print verbose log messages.")
    exclusive_arguments.add_argument("-e", "--process_email_addresses", dest="process_email_addresses",
                                     action="store_true", help="Process all the email addresses.")
    exclusive_arguments.add_argument("-t", "--test_process", dest="test_process",
                                     action="store_true", help="Run a test.")
    args = parser.parse_args()

    config = utils.configuration.get_configuration('imap_email_to_sqlite_config',
                                                   location_path=pathlib.Path('~/imap_email_to_sqlite'),
                                                   config_type=utils.configuration.CONFIGURATION_TYPE_JSON)
    if config.get('logging'):
        log_level = config['logging'].get('level')
        log_file_path = utils.common_utils.get_log_file_path(config['logging']['logs_path'],
                                                             config['logging']['log_file_basename'])
        utils.common_utils.setup_logger_to_console_file(log_file_path, log_level)
    else:
        log_file_path = None

    if args.process_email_addresses:
        process_email_addresses(config)
    elif args.test_process:
        test_process(config)
    else:
        copy_emails_from_imap_to_db(config)
        process_email_addresses(config)

    if log_file_path:
        logger.info('Log file: {}'.format(log_file_path))
    logger.info('Finished.\n')
