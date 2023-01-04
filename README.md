# Get historical reviews

Ghreviews would continue to get any review data including scores and ranks.
So you could see historical data of the reviews.

## Usages

```python
python -u main.py --cpath wwwamazoncom.cnf 
```

## Setup

### create cnf
* Example for https://www.amazon.com/gp/bestsellers/sporting-goods
```
[default]
url=https://www.amazon.com/gp/bestsellers/sporting-goods
save_interval_minutes=1440

[xpath]
items=//div[@id="gridItemRoot"]
next=//a[contains(text(), "Next page")]
score=.//i[contains(@class,"a-icon-star-small")]/span
name=.//a[@class="a-link-normal"]/span/div

reviews=.//div[@class="a-row"]//a[@class="a-link-normal"]/span
rank=.//span[@class="zg-bdg-text"]
desc=
```

items, next, score and name xpath is required at least.
Confirm xpath expressions are correct.
