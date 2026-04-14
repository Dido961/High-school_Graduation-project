# app/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

import enum

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)

    cart_items = relationship("CartItem", back_populates="user")
    orders = relationship("Order", back_populates="user")
    user_products = relationship("UserProduct", back_populates="user", cascade="all, delete-orphan")
    added_products = relationship("Product", secondary="user_products", back_populates="owners")

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50))
    stock = Column(Integer, default=0)
    image_url = Column(String(500))

    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    user_products = relationship("UserProduct", back_populates="product", cascade="all, delete-orphan")
    owners = relationship("User", secondary="user_products", back_populates="added_products")

class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, default=1)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

class PaymentStatus(enum.Enum):
    pending = 'изчакване'
    success = 'успешно'
    failed = 'отказано'

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String(20), default='Изчакване')  # логически статус на поръчката
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)  # статус на плащане
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    status = Column(String(20), default='Изчакване')
    payment_provider = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")




class UserProduct(Base):
    __tablename__ = 'user_products'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    user = relationship("User", back_populates="user_products")
    product = relationship("Product", back_populates="user_products")

