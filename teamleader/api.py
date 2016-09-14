'''
Teamleader API Wrapper class
'''

import requests
import logging
import pycountry
import datetime
import time

from teamleader.exceptions import *

logging.basicConfig(level='DEBUG')
log = logging.getLogger('teamleader.api')

base_url = "https://www.teamleader.be/api/{0}.php"
amount = 100

class Teamleader(object):

    def __init__(self, api_group, api_secret):
        log.debug("Initializing Teamleader with group {0} and secret {1}".format(api_group, api_secret))
        self.group = api_group
        self.secret = api_secret

    def _request(self, endpoint, data={}):
        log.debug("Making a request to the Teamleader API endpoint {0}".format(endpoint))
        data['api_group'] = self.group
        data['api_secret'] = self.secret
        r = requests.post(base_url.format(endpoint), data=data)
        response = r.json()
        if r.status_code == requests.codes.unauthorized:
            raise TeamleaderUnauthorizedError(message=response['reason'], api_response=r)

        if r.status_code == 505:
            raise TeamleaderRateLimitExceededError(message=response['reason'], api_response=r)

        if r.status_code == requests.codes.bad_request:
            raise TeamleaderBadRequestError(message=response['reason'], api_response=r)

        if r.status_code == requests.codes.ok:
            return r.json()

        raise TeamleaderUnknownAPIError(message=response['reason'], api_response=r)

    def get_users(self, show_inactive_users=False):
        """Getting all users.

        Args:
            show_inactive_users: 0/1 If this flag is set to 1, Teamleader will
                return also return inactive users

        Returns:
            List of dicts containing ID's and real names of all users.
        """

        return self._request('getUsers', {'show_inactive_users': int(show_inactive_users)})

    def get_departments(self):
        """Getting all departments.

        Returns:
            List of dicts containing ID's and names of all departments in your account.
        """

        return self._request('getDepartments')

    def get_tags(self):
        """Getting all tags.

        Returns:
            List of dicts containing ID's and names of all tags in your account.
        """

        return self._request('getTags')

    def get_segments(self, object_type):
        """Getting segments.

        Args:
            object_type: pick one option - crm_companies, crm_contacts, crm_todos,
                crm_callbacks, crm_meetings, inv_invoices, inv_creditnotes, pro_projects,
                sale_sales or ticket_tickets.

        Returns:
            List of dicts containing ID's and names of relevant segments in your account.
        """

        if object_type not in ['crm_companies', 'crm_contacts', 'crm_todos', 'crm_callbacks', 'crm_meetings', 'inv_invoices', 'inv_creditnotes', 'pro_projects', 'sale_sales', 'ticket_tickets']:
            raise InvalidInputError("Invalid contents of object_type.")

        return self._request('getSegments', {'object_type': object_type})

    def add_contact(self, forename, surname, email, salutation=None, telephone=None, gsm=None,
            website=None, country=None, zipcode=None, city=None, street=None, number=None,
            language=None, gender=None, date_of_birth=None, description=None, newsletter=None, tags=[],
            automerge_by_name=False, automerge_by_email=False, custom_fields={}, tracking=None,
            tracking_long=None):
        """Adding a contact to Teamleader.

        Args:
            forename: string
            surname: string
            email: string
            salutation: string
            telephone: string
            gsm: string
            website: string
            country: string: country code according to ISO 3166-1 alpha-2. For Belgium: "BE"
            zipcode: string
            city: string
            street: string
            number: string
            language: string: language code according to ISO 639-1. For Dutch: "NL"
            gender: M/F/U
            date_of_birth: datetime.date object
            description: background information on the contact
            newsletter: True/False
            tags: list of tags. Existing tags will be reused, other tags will be
                automatically created for you.
            automerge_by_name: True/False If this flag is set to True, Teamleader will merge this
                info into an existing contact with the same forename and surname, if it finds any.
            automerge_by_email: True/False If this flag is set to True, Teamleader will merge this
                info into an existing contact with the same email address, if it finds any.
            custom_fields: dict with keys the IDs of your custom fields and values the value to be set.
            tracking string: title of the activity
            tracking_long string: description of the activity

        Returns:
            ID of the contact that was added.
        """

        # get all arguments
        data = locals()
        for key in data.keys():
            if data[key] is None:
                del data[key]

        # argument validation
        if gender is not None and gender not in ['M', 'F', 'U']:
            raise InvalidInputError("Invalid contents of argument gender.")

        if type(tags) != type([]):
            raise InvalidInputError("Invalid contents of argument tags.")

        if type(custom_fields) != type({}):
            raise InvalidInputError("Invalid contents of argument custom_fields.")

        if country is not None:
            try:
                pycountry.countries.get(alpha2=country.upper())
            except:
                raise InvalidInputError("Invalid contents of argument country.")

        if language is not None:
            try:
                pycountry.languages.get(iso639_1_code=language.lower())
            except:
                raise InvalidInputError("Invalid contents of argument language.")

        if date_of_birth is not None and type(date_of_birth) != datetime.date:
            raise InvalidInputError("Invalid contents of argument date_of_birth.")


        # convert data elements that need conversion
        data['add_tag_by_string'] = ','.join(data.pop('tags'))

        for custom_field_id, custom_field_value in data.pop('custom_fields').items():
            data['custom_field_' + custom_field_id] = custom_field_value

        if date_of_birth is not None:
            data['dob'] = time.mktime(data.pop('date_of_birth').timetuple())

        if newsletter is not None:
            data['newsletter'] = int(newsletter)

        data['automerge_by_name'] = int(automerge_by_name)
        data['automerge_by_email'] = int(automerge_by_email)

        return self._request('addContact', data)

    def update_contact(self, contact_id, track_changes=True,
            forename=None, surname=None, email=None, telephone=None, gsm=None,
            website=None, country=None, zipcode=None, city=None, street=None, number=None,
            language=None, gender=None, date_of_birth=None, description=None,
            tags=[], del_tags=[], custom_fields={}, linked_company_ids=None):
        """Updating contact information.

        Args:
            contact_id: integer: ID of the contact
            track_changes: True/False: if set to True, all changes are logged and visible to users
                in the web-interfae
            forename: string
            surname: string
            email: string
            telephone: string
            gsm: string
            website: string
            country: string: country code according to ISO 3166-1 alpha-2. For Belgium: "BE"
            zipcode: string
            city: string
            street: string
            number: string
            language: string: language code according to ISO 639-1. For Dutch: "NL"
            gender: M/F/U
            date_of_birth: datetime.date object
            description: background information on the contact
            newsletter: True/False
            tags: list of tags to add. Existing tags will be reused, other tags will be
                automatically created for you.
            del_tags: list of tags to remove.
            custom_fields: dict with keys the IDs of your custom fields and values the value to be set.
        """

        # get all arguments
        data = locals()
        for key in data.keys():
            if data[key] is None:
                del data[key]

        # argument validation
        if gender is not None and gender not in ['M', 'F', 'U']:
            raise InvalidInputError("Invalid contents of argument gender.")

        if type(tags) != type([]):
            raise InvalidInputError("Invalid contents of argument tags.")

        if type(del_tags) != type([]):
            raise InvalidInputError("Invalid contents of argument tags.")

        if type(custom_fields) != type({}):
            raise InvalidInputError("Invalid contents of argument custom_fields.")

        if country is not None:
            try:
                pycountry.countries.get(alpha2=country.upper())
            except:
                raise InvalidInputError("Invalid contents of argument country.")

        if language is not None:
            try:
                pycountry.languages.get(iso639_1_code=language.lower())
            except:
                raise InvalidInputError("Invalid contents of argument language.")

        if date_of_birth is not None and type(date_of_birth) != datetime.date:
            raise InvalidInputError("Invalid contents of argument date_of_birth.")


        # convert data elements that need conversion
        data['add_tag_by_string'] = ','.join(data.pop('tags'))
        data['remove_tag_by_string'] = ','.join(data.pop('del_tags'))

        for custom_field_id, custom_field_value in data.pop('custom_fields').items():
            data['custom_field_' + custom_field_id] = custom_field_value

        if date_of_birth is not None:
            data['dob'] = time.mktime(data.pop('date_of_birth').timetuple())

        self._request('updateContact', data)


    def delete_contact(self, contact_id):
        """Deleting a contact.

        Args:
            contact_id: integer: ID of the contact
        """

        self._request('deleteContact', {'contact_id': contact_id})

    def link_contact_company(self, contact_id, company_id, function=None):
        """Deleting a contact.

        Args:
            contact_id: integer: ID of the contact
            company_id: integer: ID of the company
            function: string: the job title the contact holds at the company (eg: HR manager)
        """

        self._request('linkContactToCompany', {'contact_id': contact_id, 'company_id': company_id, 'mode': 'link', 'function': function})

    def unlink_contact_company(self, contact_id, company_id):
        """Deleting a contact.

        Args:
            contact_id: integer: ID of the contact
            company_id: integer: ID of the company
        """

        self._request('linkContactToCompany', {'contact_id': contact_id, 'company_id': company_id, 'mode': 'unlink'})

    def get_contacts(self, query=None, modified_since=None, filter_by_tag=None, segment_id=None, selected_customfields=[]):
        """Searching Teamleader contacts.

        Args:
            query: string: a search string. Teamleader will try to match each part of the
                string to the forename, surname, company name and email address.
            modified_since: integer: Unix timestamp. Teamleader will only return contacts that
                have been added or modified since that timestamp.
            filter_by_tag: string: Company tag. Teamleader will only return companies that
                have the tag.
            segment_id: integer: The ID of a segment created for contacts. Teamleader will
                only return contacts that have been filtered out by the segment settings.
            selected_customfields: comma-separated list of the IDs of the custom fields you
                wish to select (max 10).

        Returns:
            Iterator over the contacts found.
        """

        data = {}
        if query is not None:
            data['searchby'] = query
        if modified_since is not None:
            data['modifiedsince'] = modified_since
        if filter_by_tag is not None:
            data['filter_by_tag'] = filter_by_tag
        if segment_id is not None:
            data['segment_id'] = segment_id
        if len(selected_customfields) > 0:
            data['selected_customfields'] = ','.join(selected_customfields)

        there_are_more_pages = True
        pageno = 0
        while there_are_more_pages:
            page_data = {'amount': amount, 'pageno': pageno}
            page_data.update(data)
            contacts = self._request('getContacts', page_data)
            there_are_more_pages = len(contacts) > 0
            for contact in contacts:
                yield contact
            pageno += 1


    def get_contact(self, contact_id):
        """Fetching contact information.

        Args:
            contact_id: integer: ID of the contact

        Returns:
            Dictionary with contact details.
        """

        return self._request('getContact', {'contact_id': contact_id})


    def get_contacts_by_company(self, company_id):
        """Getting all contacts related to a company.

        Args:
            company_id: integer: the ID of the company

        Returns:
            Iterator over the contacts found.
        """

        contacts = self._request('getContactsByCompany', {'company_id': company_id})
        for contact in contacts:
            yield contact
