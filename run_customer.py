import json
from Customer import Customer


f = open("input_big.json")
input = json.load(f)


if __name__ == '__main__':
    output = []
    for data in input:
        if data["type"] == "customer":
            id = int(data["id"])
            events = data["events"]
            customer = Customer(id,events)
            messagesRecieved = customer.executeEvents()
            for message in messagesRecieved:
                outputData = {"id" : id, "recv" : [message]}
                output.append(outputData)
    with open("output.json", "w") as json_file:
        json_file.write("[\n")
        for i, item in enumerate(output):
            json_file.write(json.dumps(item, indent = 4))
            if i < len(output) - 1:
                json_file.write(",\n")  
            else:
                json_file.write("\n")
        json_file.write("]\n")
            
    

