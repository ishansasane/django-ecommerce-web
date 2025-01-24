from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login , logout
from django.contrib import messages
from .models import Product
import random
from django.db.models import Q
from fuzzywuzzy import fuzz
import re

# Login page logic
def home(request):
    if not request.user.is_authenticated:
        return redirect('login/')
    
    # Fetch all products
    products = Product.objects.all()

    # Shuffle the products and store them in another variable
    shuffled_products = list(products)  # Convert QuerySet to a list
    random.shuffle(shuffled_products)  # Shuffle the list

    # Pass both original and shuffled products to the template
    return render(request, 'index.html', {
        'products': products,
        'shuffled_products': shuffled_products,
    })

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
         
            login(request, user)
         
            return redirect('/')  
        else:
           
            messages.error(request, "Invalid username or password")
    
 
    return render(request, 'login_page.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        
        if User.objects.filter(username=username).exists():
            return render(request, 'register_page.html', {'error': 'Username already exists'})

        print(f"Username: {username}, Email: {email}")
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        
        return render(request, 'register_page.html', {'success': 'User registered successfully!'})
    
    return render(request, 'register_page.html')
def logoutUser(request):
    logout(request)  # This will log out the user
    return redirect('/login/')  # Redirect to the homepage or login page after logout
def normalize_text(text):
    """Normalize text for better comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    return text

def productpage(request, product_id):
    # Get the current product
    product = get_object_or_404(Product, id=product_id)

    # Normalize current product's name and description
    normalized_name = normalize_text(product.name)
    normalized_description = normalize_text(product.description)

    # Fetch all other products
    all_products = Product.objects.exclude(id=product_id)

    # Define a function to calculate similarity score
    def calculate_similarity(product_a, product_b):
        """Calculate similarity score based on keywords."""
        # Normalize names and descriptions
        name_a = normalize_text(product_a.name)
        desc_a = normalize_text(product_a.description)
        name_b = normalize_text(product_b.name)
        desc_b = normalize_text(product_b.description)

        # Check for common words in names and descriptions
        common_name_words = set(name_a.split()).intersection(name_b.split())
        common_desc_words = set(desc_a.split()).intersection(desc_b.split())

        # Calculate the similarity score based on the number of common words
        score = 0
        if len(common_name_words) >= 2:
            score += 1  # Give weight to similar names
        if len(common_desc_words) >= 3:
            score += 1  # Give weight to similar descriptions

        return score

    # List to store products with their similarity score
    product_scores = []

    # Calculate the similarity score for each product
    for p in all_products:
        score = calculate_similarity(product, p)
        if score > 0:  # Only consider products with a non-zero score
            product_scores.append((p, score))

    # Sort products by their similarity score (higher score first)
    product_scores.sort(key=lambda x: x[1], reverse=True)

    # Get the top 5 recommended products based on similarity
    recommended_products = [p[0] for p in product_scores][:5]

    # Fallback: If no recommendations, suggest random products
    if not recommended_products:
        recommended_products = all_products.order_by("?")[:5]

    # Render the product page
    return render(
        request,
        "productpage.html",
        {
            "product": product,
            "recommended_products": recommended_products,
        },
    )