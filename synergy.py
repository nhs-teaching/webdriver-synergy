import csv
import os
import time
from selenium import webdriver

class SynergySession:
    def __init__(self, uname, pw):
        self._login(uname, pw)

    def _login(self, uname, pw):
        self.browser = webdriver.Chrome()
        self.browser.get('https://wa-bsd405.edupoint.com')

        self.browser.find_element_by_id('login_name').send_keys(uname)
        self.browser.find_element_by_name('password').send_keys(pw)
        self.browser.find_element_by_name('btnLogin').click()

    def navigateToPeriod(self, period, wait=8):
        self.frame = self.browser.find_element_by_id('FRAME_CONTENT')
        self.browser.switch_to_frame(self.frame)

        nav = self.browser.find_element_by_xpath('//*[@id="dropdown_focus_container"]/a')
        rows = self.browser.find_elements_by_xpath('//*[@id="tvue_Focus"]/div[2]/table/tbody/tr/td[1]')

        for r in rows:
            if r.get_attribute('innerHTML') == period:
                webdriver.ActionChains(self.browser).move_to_element(nav).click().move_to_element(r).click().perform()
                break

        time.sleep(wait)

    def _countStudents(self):
        students = self.browser.find_elements_by_xpath("(//*[@id='StudentChart']/table/tbody/tr/td/*[contains(@class, 'Student')])")
        self.student_count = len(students)

    def _scrapeStudentHistory(self, csv_writer):
        # Find the name of the student
        name_element = self.browser.find_element_by_xpath('//*[@id="PrimaryView"]/div[1]/div[3]/div/div/div[1]')

        rows = self.browser.find_elements_by_xpath('//*[@id="PrimaryView"]/div[2]/div/div/div/div[2]/div/div[1]/table[2]/tbody/tr')

        for r in rows:
            line = r.find_element_by_xpath('td[1]')
            year = r.find_element_by_xpath('td[2]/div[2]/span')
            title = r.find_element_by_xpath('td[4]/div[2]/span')
            cid = r.find_element_by_xpath('td[5]/div[2]/span')
            grade = r.find_element_by_xpath('td[6]/div[2]/span')
            mark = r.find_element_by_xpath('td[7]/div[2]/span')

            csv_writer.writerow([name_element.text, year.text, title.text, cid.text, grade.text, mark.text])

        # Pagination
        try:
            next_page = self.browser.find_element_by_xpath('//*[@id="PrimaryView"]/div[2]/div/div/div/div[2]/ul[1]/li[contains(@class, "active")]/following-sibling::li/a')
            next_page.click()
            time.sleep(3)
            self._scrapeStudentHistory(csv_writer)
        except:
            pass

    def iterateStudents(self, csv_file):
        self._countStudents()
        for i in range(self.student_count):
            student = self.browser.find_element_by_xpath("(//*[@id='StudentChart']/table/tbody/tr/td/*[contains(@class, 'Student')])[" + str(i + 1) + "]")

            # Click on the first student
            student.click()
            time.sleep(1)

            # Store the parent window handle
            window_parent = self.browser.current_window_handle

            # Find the menu item
            self.browser.find_element_by_xpath('//*[@id="StudentActionMenu"]/div/ul/li[4]').click()
            time.sleep(1)

            # Switch context to the new window
            window_history = self.browser.window_handles[1]
            self.browser.switch_to_window(window_history)
            time.sleep(3)

            self._scrapeStudentHistory(csv_file)

            # Go to paren
            self.browser.close()
            self.browser.switch_to_window(window_parent)
            self.browser.switch_to_frame(self.frame)
            time.sleep(1)


def main():
    s = SynergySession(os.environ.get('SYNERGY_UNAME'), os.environ.get('SYNERGY_PW'))

    #TODO: command line arg
    s.navigateToPeriod('7')

    with open('student_history.csv', 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        s.iterateStudents(csvwriter)

    s.browser.quit()

if __name__ == "__main__":
    main()
