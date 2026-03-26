#include <stdio.h>

void convertDays(int days)
{
       int year = 1980;
       while (days > 365)
       {
              if (isLeapYear(year))
              {
                     if (days > 366)
                     {
                            days -= 366;
                            year += 1;
                     }
              }
              else
              {
                     days -= 365;
                     year += 1;
              }
       }
}