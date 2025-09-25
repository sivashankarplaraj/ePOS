SELECT 
    t1.PRODNUMB,
    p1.PRODNAME AS MainProdName,
    t1.OPT_PRODNUMB,
    p2.PRODNAME AS OptProdName
FROM update_till_pchoice t1
JOIN update_till_prodext p1 
    ON t1.PRODNUMB = p1.PRODNUMB
JOIN update_till_prodext p2
    ON t1.OPT_PRODNUMB = p2.PRODNUMB
ORDER BY t1.PRODNUMB;


SELECT 
    p.PRODNUMB,
    p.PRODNAME,
    p.ITEM_DESC,
    GROUP_CONCAT(t.MENU_DESC, ', ') AS Toppings
FROM update_till_eposprod p
JOIN update_till_acodes a 
    ON p.PRODNUMB = a.PRODNUMB
JOIN update_till_toppingdel t
    ON a.ST_CODENUM = t.ACODE
GROUP BY 
    p.PRODNUMB,
    p.PRODNAME,
    p.ITEM_DESC
HAVING COUNT(t.ACODE) > 1
ORDER BY 
    p.PRODNUMB;

-- Explanation
-- GROUP BY groups toppings per product.
-- COUNT(t.ACODE) counts the number of toppings per product.
-- HAVING COUNT(t.ACODE) > 1 filters out products with only one or zero toppings.