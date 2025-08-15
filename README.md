# 🧩 Palm Wallet - Industry Level MVP

A modern palm-based payment system built with Flask, SQLite3, and HTML5/CSS3/JavaScript. This MVP demonstrates a complete payment ecosystem with user and merchant interfaces.

## 🚀 Features

### User Interface
- ✅ Phone number-based Signup/Login (via OTP via SMS)
- ✅ Register full name & phone number
- ✅ **AI Palm Detection & Capture** (using MediaPipe Hands)
- ✅ Show static Palm Wallet with balance
- ✅ Add money (via OTP simulation)
- ✅ View Transaction History

### Merchant Interface
- ✅ Signup/Login via phone number & OTP simulation
- ✅ Legal business info required
- ✅ Create payment request (amount, note)
- ✅ Trigger Palm Scan (simulated)
- ✅ Deduct amount from user, add to merchant wallet
- ✅ View Merchant transaction history

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **AI/ML**: MediaPipe Hands for palm detection
- **Styling**: Modern CSS with gradients and animations
- **File Upload**: Palm image storage with AI validation
- **Authentication**: Session-based with OTP simulation

## 📁 Project Structure

```
Palpe/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Modern CSS styling
│   ├── js/
│   │   ├── script.js     # JavaScript functionality
│   │   └── palm-detection.js # AI palm detection
│   └── uploads/          # Palm image storage
├── templates/
│   ├── user_signup.html      # User registration
│   ├── user_login.html       # User login
│   ├── dashboard_user.html   # User dashboard
│   ├── merchant_signup.html  # Merchant registration
│   ├── merchant_login.html   # Merchant login
│   ├── dashboard_merchant.html # Merchant dashboard
│   └── payment_scan.html     # Payment processing
├── database/
│   └── db.sqlite3        # SQLite database
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   # Navigate to project directory
   cd Palpe
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your browser and go to: `http://localhost:5000`
   - The application will start with the user login page

## 🎯 How to Use

### For Users

1. **Register as a User**
   - Go to `/user/signup`
   - Enter your phone number and full name
   - **Use AI Palm Detection**: Click "Start Camera" to open camera
   - Position your palm in the frame (AI will detect and guide you)
   - Click "Capture Palm" when AI confirms palm detection
   - Click "Register"

2. **Login**
   - Go to `/user/login`
   - Enter your phone number
   - Click "Send OTP" to get a simulated OTP
   - Enter the OTP and login

3. **Use Your Wallet**
   - View your wallet balance
   - Add money to your wallet
   - View transaction history

### For Merchants

1. **Register as a Merchant**
   - Go to `/merchant/signup`
   - Enter business information (name, address, license)
   - Click "Register Business"

2. **Login**
   - Go to `/merchant/login`
   - Enter business phone number
   - Use OTP simulation to login

3. **Accept Payments**
   - Create payment requests with amount and note
   - Trigger palm scan simulation
   - Process payments from users

## 🔧 Database Schema

### Users Table
- `id`: Primary key
- `phone_number`: Unique phone number
- `full_name`: User's full name
- `palm_image`: Path to uploaded palm image
- `wallet_balance`: Current wallet balance
- `created_at`: Registration timestamp

### Merchants Table
- `id`: Primary key
- `phone_number`: Business phone number
- `business_name`: Business name
- `business_address`: Business address
- `business_license`: License number
- `wallet_balance`: Merchant wallet balance
- `created_at`: Registration timestamp

### Transactions Table
- `id`: Primary key
- `transaction_type`: Type (DEPOSIT, PAYMENT, etc.)
- `from_user_id`: User making payment
- `to_merchant_id`: Merchant receiving payment
- `amount`: Transaction amount
- `description`: Transaction description
- `created_at`: Transaction timestamp

## 🎨 Features Highlight

### Modern UI/UX
- Responsive design that works on all devices
- Beautiful gradient backgrounds
- Smooth animations and transitions
- Professional card-based layout

### Security Features
- Session-based authentication
- OTP simulation for secure login
- **AI-powered palm validation**
- File upload validation
- SQL injection protection

### Payment Processing
- Real-time balance updates
- Transaction history tracking
- Palm scan simulation
- Payment request creation

## 🔮 Future Enhancements

### Phase 2 Features (Planned)
- Real OTP integration with SMS services
- Actual palm vein scanning technology
- Bank API integration for real money transfers
- Mobile app development
- Advanced security features
- Multi-currency support
- Analytics dashboard

### Technical Improvements
- RESTful API development
- Docker containerization
- CI/CD pipeline
- Unit and integration tests
- Performance optimization
- Scalable database (PostgreSQL/MySQL)

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in app.py
   app.run(debug=True, port=5001)
   ```

2. **Database errors**
   ```bash
   # Delete database file and restart
   rm database/db.sqlite3
   python app.py
   ```

3. **File upload issues**
   - Ensure `static/uploads/` directory exists
   - Check file permissions
   - Verify file size (max 5MB)

## 📝 Development Notes

### OTP Simulation
- Current implementation generates random 6-digit OTPs
- In production, integrate with SMS services like Twilio
- OTP validation should include expiration time

### AI Palm Detection
- **Real-time palm detection** using MediaPipe Hands
- **Live camera preview** with palm landmark visualization
- **Intelligent palm positioning** guidance
- **Automatic capture** when palm is properly positioned
- Real implementation would use palm vein scanning hardware
- Biometric matching algorithms would be implemented

### Security Considerations
- Use HTTPS in production
- Implement proper session management
- Add rate limiting for OTP requests
- Encrypt sensitive data in database

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and demonstration purposes. Feel free to use and modify as needed.

## 📞 Support

For questions or issues:
- Check the troubleshooting section
- Review the code comments
- Test with different scenarios

---

**Built with ❤️ using Flask, SQLite3, and modern web technologies**
