import xmlrpc.client

import time
import socket
#python server.py
#python client.py
MAX_RETRIES = 3
RETRY_DELAY = 5


def print_menu():
    print("\n===== Distributed Notebook Client =====")
    print("1. Add a note")
    print("2. Get notes by topic")
    print("3. Add Wikipedia info to a topic")
    print("4. Exit")
    print("\n")

def connect_to_server():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            proxy = xmlrpc.client.ServerProxy("http://localhost:9000", allow_none=True)
            proxy.system.listMethods()
            return proxy
        except (socket.gaierror, ConnectionRefusedError):
            print(f"Error: Cannot connect to the server. Make sure the server is running and reachable. (Attempt {retries+1}/{MAX_RETRIES})")
        except TimeoutError:
            print(f"Error: Connection to server timed out. (Attempt {retries+1}/{MAX_RETRIES})")
        except xmlrpc.client.ProtocolError as e:
            print(f"Protocol Error: {e} (Attempt {retries+1}/{MAX_RETRIES})")
        except xmlrpc.client.Fault as e:
            print(f"XML-RPC Fault: {e} (Attempt {retries+1}/{MAX_RETRIES})")
        except Exception as e:
            print(f"Unexpected error: {e} (Attempt {retries+1}/{MAX_RETRIES})")

        retries += 1
        if retries < MAX_RETRIES:
            print(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            print("Failed to connect to the server after multiple attempts. Please check if the server is running.")
            return None

def main():
    proxy = connect_to_server()
    if proxy is None:
        return

    try:
        while True:
            print_menu()
            choice = input("Enter your choice: ")
            if choice == '1':
                topic = input("Topic: ")
                text = input("Note content: ")
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    success = proxy.add_note(topic, text, timestamp)
                    if success:
                        print(f"Note added to topic '{topic}'.")
                    else:
                        print("Failed to add note.")
                except Exception as e:
                    print(f"Network error while adding note: {e}")

            elif choice == '2':
                topic = input("Topic: ")
                try:
                    notes = proxy.get_topic_contents(topic)
                    if notes:
                        print(f"Notes in '{topic}':")
                        for i, note in enumerate(notes, 1):
                            print(f"Note {i}")
                            print(f"Timestamp: {note['timestamp']}")
                            print(f"Content: {note['text']}\n")
                    else:
                        print(f"No notes found for '{topic}'.")
                except Exception as e:
                    print(f"Network error while fetching notes: {e}")

            elif choice == '3':
                topic = input("Topic: ")
                keyword = input("Wikipedia keyword: ")
                try:
                    result = proxy.add_wikipedia_info(topic, keyword)
                    print(result)
                except Exception as e:
                    print(f"Network error while fetching Wikipedia info: {e}")

            elif choice == '4':
                print("Exiting client.")
                break
            else:
                print("Invalid choice.")
    except KeyboardInterrupt:
        print("\nClient interrupted. Exiting gracefully...")

if __name__ == "__main__":
    main()
