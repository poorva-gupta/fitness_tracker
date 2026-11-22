import razorpay
import os
razorpay_client=razorpay.Client(auth=(os.getenv("RAZOR_APIKEY"),os.getenv("RAZOR_SECRET")))
