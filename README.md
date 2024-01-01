# Automatic label from Google Vision API

## Demo

For launch this code, you can enter this following command : 

```bash
python3 google_vision.py [folder_name] [name.json] -u [url_supabase] -k [key_supabase_service_role] -b [bucket_from_supabase_name] -n [number_word_flabel]
```

## All parameters

- `folder_name` : Enter folder name to racine root from your google_api.py
- `name.json` : Enter name file of the name.json you can get in Google API. This is your .json key for authentification. this is a example of this .json bellow : 

```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "8e53616858...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMII18k=\n-----END PRIVATE KEY-----\n",
  "client_email": "googleapike...",
  "client_id": "1099719...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/googleapikey%40...",
  "universe_domain": "googleapis.com"
}
```
- `url_supabase` : url supabase link you can find on your account. Need this for create public link for all your picture
- `key_supabase_service_role` : Enter your key supabase service role from your supabase account.
> [!WARNING]\
> It's very important to enter **SERVICE ROLE** key and not **ANON KEY**, or then RLS will block update picture
- `bucket_from_supabase_name` : Enter name of a bucket in supabase.
> [!WARNING]\
> This bucket need to be a **Public bucket** and not a **Private bucket** !
- `number_word_flabel` : Enter a int number for choice how many word label you want for one picture
