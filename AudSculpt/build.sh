# Exit immediately if a command fails
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setting permissions on static files..."
chmod -R 755 staticfiles/
