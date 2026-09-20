import csv

print("IT Help Desk Ticket Analyzer")
tickets = [
    {
    "id": 1001,
    "category": "Password Reset",
    "priority": "Medium",
    "status": "open"
},
{ "id": 1002,
 "category": "Software",
 "priority": "High",
 "status": "pending"
}
]
def load_tickets():
     tickets = []
     with open("tickets.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
             ticket = {
                 "id": int(row["id"]),
                 "category": row["category"],
                 "priority": row["priority"],
                 "status": row["status"]
             }
             tickets.append(ticket)
def display_tickets(tickets):
        for ticket in tickets:
            print("Ticket ID:", ticket["id"])
            print("Category:", ticket["category"])
            print("Priority:", ticket["priority"])
            print("Status:", ticket["status"])
            print("--------------------")
def analyze_tickets(tickets):
    open_count = 0
    closed_count = 0
    pending_count = 0
    high_priority_count = 0
    for ticket in tickets:
                if ticket["status"] == "open":
                    open_count += 1
                elif ticket["status"] == "closed":
                    closed_count += 1
                elif ticket["status"] == "pending":
                    pending_count += 1   
                if ticket["priority"] == "High":
                    high_priority_count += 1
    return open_count, closed_count, pending_count, high_priority_count
def search_ticket(tickets, search_id):
    for ticket in tickets:
        if ticket["id"] == search_id:
            return ticket 
    return None

def main():
    try:
        search_id = int(input("Enter Ticket ID: "))
    except ValueError:
        print("Please enter a valid numeric Ticket ID.")
        search_id = None
    display_tickets(tickets)
    open_count, closed_count, pending_count, high_priority_count = analyze_tickets(tickets)
    print("Total Open Tickets:", open_count)
    print("Total Closed Tickets:", closed_count)
    print("Total Pending Tickets:", pending_count)
    print("Total High Priority Tickets:", high_priority_count)
    if search_id is not None:
            found_ticket = search_ticket(tickets, search_id)
            if found_ticket is not None:
                print("Ticket Found:")
                print("Ticket ID:", found_ticket["id"])
                print("Category:", found_ticket["category"])
                print("Priority:", found_ticket["priority"])
                print("Status:", found_ticket["status"])
            else:
                print("Ticket not found.")
main()
   