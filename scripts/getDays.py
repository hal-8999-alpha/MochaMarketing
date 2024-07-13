import pinecone
import sys
import json

def extract_day_number(metadata):
    try:
        day_string = metadata['Day']
        # Check if the day field starts with 'Day'
        if day_string.startswith('Day '):
            return int(day_string.split(' ')[1])
        else:
            # Assume it's a number if it doesn't start with 'Day'
            return int(day_string)
    except (KeyError, ValueError, IndexError) as e:
        print(f'Failed to extract day number from metadata: {metadata}. Error: {e}')
        return -1  # default value

def get_days(api_key, environment, index_name, calendarId, day_string=None):

    pinecone.init(api_key=api_key, environment=environment)

    print(day_string)
    print(calendarId)

    # Connect to the index
    index = pinecone.Index(index_name=index_name)

    # Define the query vector (you may need to adjust the dimension and values)
    query_vector = [0] * 1536  

    # Define the filter
    filter = {'$and': [
        {'Calendar Id': {'$eq': calendarId}},
        {'Type': {'$eq': 'Day'}},
        {'Active': {'$eq': 'Yes'}},
    ]}

    # If a day_string is provided, add it to the filter
    if day_string is not None and day_string != '':
        days = day_string.split(',')
        filter['$and'].append({'Approved': {'$eq': 'Yes'}})
        filter['$and'].append({'Day': {'$in': days}})

    print(filter)

    query_result = index.query(
        vector=query_vector,
        filter=filter,
        top_k=100,
        include_metadata=True
    )

    print(query_result.matches)

    # Sort the query results by the "Day" metadata in ascending order
    sorted_results = sorted(query_result.matches, key=lambda x: extract_day_number(x.metadata))

    print(sorted_results)

    # Print the Day and Content metadata of the top 7 results
    json_data = {
        "days": [
            {
                "day": match.metadata["Day"],
                "metadata": match.metadata,
                "content": match.metadata["Content"],
                "id": match.id
            }
            for match in sorted_results
        ],
    }

    return json_data

if __name__ == "__main__":

    api_key, environment, index_name, calendarId, day_string = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
    days_data = get_days(api_key, environment, index_name, calendarId, day_string)
    print(json.dumps(days_data))  # Output data as JSON string
