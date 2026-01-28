import datetime


class Ticket:
    """ A parking ticket by the parking dispenser

    """

    def __init__(self):
        self.id = 0     # TODO: add a function to generate unique ticket id
        self.ts_in = datetime.datetime.now()
        self.ts_out = None

    def get_parking_duration(self) -> float:
        """ return parking hours
        """
        self.ts_out = datetime.datetime.now()

        td = self.ts_out - self.ts_in

        return td.seconds / 3600

    def get_ticket_id(self):
        return self.id


class Entrance:
    """ A parking ticket dispenser

    """

    def __init__(self, entrance_id=""):
        self.entrance_id = entrance_id

    def check_in(self):
        _ticket = Ticket()
        _id = _ticket.get_ticket_id()
        # print the ticket with BAR code with _id encoded
        return _ticket


class ExitKiosk:
    """

    """

    def __init__(self, exit_id=""):
        self.exit_id = exit_id

    def validate_ticket(self):
        # Get the ticket_id from BAR code reader

        # Search for the ticket

        # call get_parking_duration()

        # call the billing system for payment

        # open gate if having permission
        return True


class ParkingSystem:
    """ A parking lot system with slot occupation auto-sensing

    """

    slot_size = {"Handicap": [0, 0],
                 "Normal": [0, 0],
                 "Compact": [0, 0]
                 }
    slots = dict()
    tickets = dict()

    entrance1 = Entrance("East")
    entrance2 = Entrance("South")
    exit1 = ExitKiosk("East")

    @classmethod
    def initialize_parking_slots(cls):
        """ Fill the slots dictionary

        :return:
        """

        # Fill cls.slots. Input could be CSV/JSON/XML files, or SQL interface
        cls.slots['000001'] = {'floor': 'First',
                               'section': 'A',
                               'lane': 1,
                               'size': 'Compact',
                               'state': '0'
                               }

    @classmethod
    def display_empty_slots(cls):
        """ Calculate number of empty slots for each size and display them

        :return:
        """

        for size in cls.slot_size.keys():
            cls.slot_size[size][1] = len(list(filter(
                lambda x: cls.slots[x]['state'] == '0' and cls.slots[x]['size'] == size, cls.slots
            )))
            print(f'{size}: {cls.slot_size[size][1]}')


if __name__ == '__main__':
    ParkingSystem.initialize_parking_slots()
    ParkingSystem.display_empty_slots()
