import React, { createContext, useContext, useState, useEffect } from 'react';

// 1. Create the Context (the vault)
const CartContext = createContext();

// 2. Create the Provider (the manager of the vault)
export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);

  // Load cart from localStorage when the app first loads so items aren't lost on refresh
  useEffect(() => {
    const savedCart = localStorage.getItem('happy-pet-cart');
    if (savedCart) {
      setCartItems(JSON.parse(savedCart));
    }
  }, []);

  // Save to localStorage every time the cartItems array changes
  useEffect(() => {
    localStorage.setItem('happy-pet-cart', JSON.stringify(cartItems));
  }, [cartItems]);

  // Function to add a product to the cart
  const addToCart = (product) => {
    const existingItem = cartItems.find((item) => item.id === product.id);
    
    if (existingItem) {
      // If it exists, just increase the quantity
      setCartItems(
        cartItems.map((item) => 
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        )
      );
    } else {
      // If it's new, add it to the cart array with a quantity of 1
      setCartItems([...cartItems, { ...product, quantity: 1 }]);
    }
  };

  return (
    <CartContext.Provider value={{ cartItems, addToCart }}>
      {children}
    </CartContext.Provider>
  );
};

// 3. A custom hook to easily access the cart from any file
export const useCart = () => useContext(CartContext);