# Exit immediately if a command fails
set -e

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply database migrations
echo "Applying migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Ensure correct permissions on static files directory
echo "Setting permissions on static files..."
chmod -R 755 staticfiles/
