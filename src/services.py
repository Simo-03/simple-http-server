import re


def validate_user_id(user_id: str):
    # Letters, digits, and underscores; at least one character
    user_id_pattern = r"[A-Za-z0-9_]+"
    if re.fullmatch(user_id_pattern, user_id) is None:
        raise ValueError("invalid username format")



def validate_country(country: str):
    # Exactly two lowercase ASCII letters
    country_pattern = r"[a-z]{2}"   
    if re.fullmatch(country_pattern, country) is None:
        raise ValueError("invalid username format")

def validate_city(city: str):
    # Lowercase words separated by single underscores
    city_pattern = r"[a-z]+(?:_[a-z]+)*"
    if re.fullmatch(city_pattern, city) is None:
            raise ValueError("invalid username format")


def username_parser(username: str):
    if not username:
        raise ValueError("invalid username format")

    if "_city_" in username:
        if "_c_" not in username:
            raise ValueError("invalid username format")
        
        else:
            user_id, _, addr = username.partition("_c_")

            if not addr:
                raise ValueError("invalid username format")
            
            country, _, city = addr.partition("_city_")

            validate_user_id(user_id)
            validate_country(country)
            validate_city(city)
            return (user_id, country, city)

    elif "_c_" in username:
        user_id, _, country = username.partition("_c_")

        validate_user_id(user_id)
        validate_country(country)
        return (user_id, country, None)
    
    else:
        user_id = username

        validate_user_id(user_id)
        return (user_id, None, None)


