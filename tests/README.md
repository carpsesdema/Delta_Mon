# 🚀 DeltaMon Setup Guide for Pradeep

## 📋 Quick Start (3 Steps)

### 1️⃣ **Initial Setup**
```bash
# Run this FIRST to set up your configuration
python setup_config.py
```
This creates your personal config file with alert thresholds.

### 2️⃣ **Configure Your Alerts** 
```bash
# Run the main app
python main.py
```
- Click **"⚙️ Configure Alerts"** button
- Set your exact thresholds (currently +0.08 / -0.05)
- Add your Discord webhook URL
- Save settings

### 3️⃣ **Start Monitoring**
- Click **"📋 Read Accounts from Dropdown"** → Finds all 25 accounts
- Click **"🚀 Start Enterprise Monitoring"** → Begins monitoring
- Get alerts when delta thresholds are exceeded!

---

## ⚙️ Alert Configuration

### 🎯 **Current Default Thresholds:**
- **High Delta Alert**: When delta > **+0.08**
- **Low Delta Alert**: When delta < **-0.05**

### 📊 **Examples:**
```
Delta = +0.09 → 🚨 HIGH DELTA ALERT (above +0.08)
Delta = +0.07 → ✅ No alert (below +0.08)
Delta = +0.00 → ✅ No alert (between thresholds)
Delta = -0.04 → ✅ No alert (above -0.05)
Delta = -0.06 → 🚨 LOW DELTA ALERT (below -0.05)
```

### 🔧 **How to Change Thresholds:**
1. **Via GUI**: Click "⚙️ Configure Alerts" in main app
2. **Via File**: Edit `pradeep_config.ini` directly
3. **Via Setup**: Run `python setup_config.py` again

---

## 🔔 Discord Setup

### **Get Your Discord Webhook URL:**
1. Go to your Discord server
2. Right-click channel → **Settings** → **Integrations** 
3. Click **"Create Webhook"**
4. Copy the webhook URL
5. Paste it in DeltaMon configuration

### **Test Your Discord:**
- Use **"🧪 Test Webhook"** button in configuration
- Should see test message in your Discord channel

---

## 📖 How It Works

### **Account Discovery:**
1. Finds your ToS window automatically
2. Clicks the account dropdown
3. Reads all 25 account names via OCR
4. No manual configuration needed!

### **Delta Monitoring:**
1. Switches between accounts automatically  
2. Finds your "OptionDelta" column
3. Extracts decimal values like `-0.05`, `1.0`
4. Compares against your thresholds
5. Sends Discord alerts when exceeded

### **Smart Features:**
- **Rate limiting**: Max 1 alert per account per 5 minutes
- **Parallel scanning**: Monitors multiple accounts simultaneously  
- **Error resilience**: Continues monitoring if some accounts fail
- **Health tracking**: Knows which accounts are responsive

---

## 🧪 Testing

### **Test Without Money:**
```bash
# Test dropdown reading
python test_dropdown_reading.py

# Test alert thresholds  
python test_thresholds.py

# Test with your screenshot
python test_with_screenshot.py
```

### **Screenshot Testing:**
- Save your ToS screenshot as `pradeep_screenshot.png`
- Run screenshot test to verify delta extraction
- No need for real money in accounts!

---

## 📁 Important Files

```
pradeep_config.ini     # Your personal configuration
assets/templates/      # Dropdown detection templates  
assets/captures/       # Debug images and screenshots
debug_images/          # OCR analysis images
```

---

## 🔧 Configuration Options

### **Alert Thresholds:**
- `positive_threshold` = Alert when delta > this value
- `negative_threshold` = Alert when delta < this value

### **Monitoring Speed:**
- `scan_interval_seconds` = Time between full scans (45s default)
- `fast_mode` = Skip some validations for speed
- `parallel_scanning` = Monitor multiple accounts at once

### **Alert Behavior:**
- `alert_cooldown_minutes` = Min time between alerts per account (5m)
- `max_alerts_per_hour` = Prevent spam (20 default)

---

## ❓ FAQ

### **Q: What if thresholds are wrong?**
A: Use "⚙️ Configure Alerts" to adjust anytime. Changes apply immediately.

### **Q: Can I test without real money?**
A: Yes! Use the screenshot testing tools to verify everything works.

### **Q: What if it can't find my accounts?**
A: Run "🎯 Setup Template" first to improve dropdown detection.

### **Q: What if delta extraction fails?**
A: Check that your "OptionDelta" column is visible and properly configured in ToS.

### **Q: How do I change Discord channel?**
A: Create new webhook in different channel, update URL in configuration.

---

## 🎯 Recommended Workflow

1. **First Time Setup:**
   - Run `python setup_config.py`
   - Configure Discord webhook
   - Test with `python test_dropdown_reading.py`

2. **Daily Use:**
   - Start DeltaMon app
   - Click "📋 Read Accounts from Dropdown" 
   - Click "🚀 Start Enterprise Monitoring"
   - Let it run and get Discord alerts!

3. **Adjustments:**
   - Use "⚙️ Configure Alerts" as needed
   - Monitor performance in Statistics panel
   - Check logs for any issues

---

**🎉 Ready to monitor your 25 accounts with custom delta thresholds!**