import boto3
import os

TABLE_NAME = "users"
AWS_REGION = "eu-north-1"
BUCKET_NAME = "yoavbucketusers"


dynamodb = boto3.client(
    "dynamodb",
    region_name=AWS_REGION,
)
s3_client = boto3.client(
    "s3",
    region_name="us-west-2",
)

rekognition_client = boto3.client("rekognition", region_name="us-west-2")


def upload_picture(file, key=None):
    filename = file.filename if not key else os.path.join(key, file.filename)
    s3_client.upload_fileobj(file, BUCKET_NAME, filename)
    profile_picture = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
    return profile_picture


def delete_picture(key=None):
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
    return True


def save_user_data(data):
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            "first_name": {"S": data["first_name"]},
            "last_name": {"S": data["last_name"]},
            "email": {"S": data["email"]},
            "phone_number": {"S": data["phone_number"]},
            "height": {"S": data["height"]},
            "age": {"S": str(data["age"])},
            "gender": {"S": data["gender"]},
            "hobby": {"S": data["hobby"]},
            "education": {"S": data["education"]},
            "designation": {"S": data["designation"]},
            "profile_picture": {"S": data["profile_picture"]},
            "bio": {"S": data["bio"]},
        },
    )
    return True


def get_user(email):
    data = dynamodb.get_item(TableName=TABLE_NAME, Key={"email": {"S": email}})
    data = data.get("Item")
    if data:
        return convert_to_dict(data)
    return None


def get_user_by_image(url):
    data = dynamodb.scan(
        TableName=TABLE_NAME,
        FilterExpression="profile_picture = :val",
        ExpressionAttributeValues={":val": {"S": url}},
    )
    data = data.get("Items")
    if data:
        user_info = convert_to_dict(data[0])
        return user_info
    return None


def get_image_list():
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
    target_images = [obj["Key"] for obj in response.get("Contents", [])]
    return target_images


def compare_faces(source_image_path, target_image):
    response = rekognition_client.compare_faces(
        SourceImage={"S3Object": {"Bucket": BUCKET_NAME, "Name": source_image_path}},
        TargetImage={"S3Object": {"Bucket": BUCKET_NAME, "Name": target_image}},
        SimilarityThreshold=80,
    )

    return response.get("FaceMatches", [])


# Function to generate S3 object URL
def get_file_url(key):
    url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
    return url


def filter_data(data):
    filter_expression_parts = []
    expression_attribute_values = {}

    for column_name, value in data.items():
        expression_key = f":{column_name}"
        filter_expression_parts.append(f"{column_name} = {expression_key}")
        expression_attribute_values[expression_key] = {"S": value}

    filter_expression = " AND ".join(filter_expression_parts)

    response = dynamodb.scan(
        TableName=TABLE_NAME,
        FilterExpression=filter_expression,
        ExpressionAttributeValues=expression_attribute_values,
    )

    items = response.get("Items")
    if items:
        items = [convert_to_dict(item) for item in items]
        return items
    else:
        return []


def convert_to_dict(data):
    user_info = {
        "first_name": data["first_name"]["S"],
        "last_name": data["last_name"]["S"],
        "email": data["email"]["S"],
        "phone_number": data["phone_number"]["S"],
        "height": data["height"]["S"],
        "age": data["age"]["S"],
        "gender": data["gender"]["S"],
        "hobby": data["hobby"]["S"],
        "education": data["education"]["S"],
        "designation": data["designation"]["S"],
        "profile_picture": data["profile_picture"]["S"],
        "bio": data["bio"]["S"],
    }
    return user_info
