import React, { createContext, useContext, useState, useEffect } from 'react';

const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);

  useEffect(() => {
    const savedCart = localStorage.getItem('happy-pet-cart');
    if (savedCart) {
      setCartItems(JSON.parse(savedCart));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('happy-pet-cart', JSON.stringify(cartItems));
  }, [cartItems]);

  // CRITICAL FIX: Now accepts the selected variant alongside the product
  const addToCart = (product, selectedVariant) => {
    if (!selectedVariant) return;

    // Create a unique ID for the cart so different sizes/colors don't merge
    const cartItemId = `${product.id}-${selectedVariant.id}`;
    
    const existingItem = cartItems.find((item) => item.cartItemId === cartItemId);
    
    if (existingItem) {
      setCartItems(
        cartItems.map((item) => 
          item.cartItemId === cartItemId ? { ...item, quantity: item.quantity + 1 } : item
        )
      );
    } else {
      setCartItems([...cartItems, { ...product, cartItemId, selectedVariant, quantity: 1 }]);
    }
  };

  return (
    <CartContext.Provider value={{ cartItems, addToCart }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => useContext(CartContext);