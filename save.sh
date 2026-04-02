#!/bin/bash
git add .
read -p "Update message: " msg
git commit -m "${msg:-'Automated update'}"
git push origin main
echo "✅ Backup complete!"
