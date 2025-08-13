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
